import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from ..helpers import get_bin, execute_sys_command

_logger = logging.getLogger(__name__)

current_path = os.path.join(os.path.dirname(os.path.abspath(__file__))) + "/.."

TTL = 1200


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    domain = fields.Char(string=_("Domain"))
    kubectl = fields.Char(string=_("Kubectl Path"), compute='_get_bin_path')
    awscli = fields.Char(string=_("Kubectl Path"), compute='_get_bin_path')
    database_password = fields.Char(string=_("Database password"))
    code_lower = fields.Char(string=_("Code Losercase"), compute='_get_code_lower_case')
    admin_password = fields.Char(string=_("Admin Password"))
    instance_status = fields.Selection(selection=[
        ('not_created', 'Not Created'),
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('failed', 'Failed'),
        ('error', 'Error'),
        ('unknown', 'Unknown'),
        ('waiting', 'Waiting'),
        ('terminating', 'Terminating'),
        ('terminated', 'Terminated'),
        ('containercreating', 'Creating'),
        ('crashloopbackoff', 'Crashed'),
        ('removed', 'Removed')
    ], string=_('Instance Status'), compute='_get_instance_status')

    description_payment = fields.Html(string='Description Confirm Payment', translate=True)
    check_confirm_payment = fields.Boolean(string='Check Confirm Payment', default=False)

    def unlink(self):
        try:
            self.cleanup_vive_software()
        except Exception as e:
            pass
        return super(SaleSubscription, self).unlink()

    @api.model
    def _cron_cleanup_closed_subscription(self):
        period_active = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.period_active', 0))
        self.clean_up_instance_periodically(period_active, 'closed')

    @api.model
    def _cron_cleanup_ended_trial_subscription(self):
        period_active = int(self.env['ir.config_parameter'].sudo().get_param('onnet_custom_subscription.period_trial', 0))
        self.clean_up_instance_periodically(period_active, 'trial')
        self.send_email_expired_trial_databases(period_active)

    @api.model
    def clean_up_instance_periodically(self, period, stage):
        expired_date = datetime.now().date() + timedelta(days=period)
        to_clean_subs = self.env['sale.subscription'].search([
            ('stage_id.category', '=', stage),
            ('recurring_next_date', '<=', expired_date),
        ])
        # FIXME: should create a field to mark sub as cleaned or create a new stage to say that instance was cleared
        to_clean_subs = to_clean_subs.filtered(lambda x: x.instance_status != 'not_created')
        for sub in to_clean_subs:
            sub.cleanup_vive_software()

    def _get_instance_status(self):
        instance_status = {}
        env = os.environ.copy()
        aws_bin = self[0].awscli.strip("/aws")
        env['PATH'] = env["PATH"] + ":/%s" % aws_bin
        output, err = execute_sys_command(" ".join([
            self[0].kubectl,
            'get',
            'pods',
            '-A',
        ]), env=env, shell=True)
        status = str(output).split('\\n')
        for s in status[1:len(status) - 1]:
            s = " ".join(s.split()).split(" ")
            instance_status[s[0]] = s[3].lower()
        for sub in self:
            if sub.code_lower not in instance_status and sub.is_check_delete_instance == True:
                sub.instance_status = 'removed'
            elif sub.code_lower not in instance_status:
                sub.instance_status = 'not_created'
            else:
                sub.instance_status = instance_status[sub.code_lower]

    def _get_code_lower_case(self):
        for subscription in self:
            subscription.code_lower = subscription.code.lower()

    @api.model
    def _get_bin_path(self):
        for subscription in self:
            subscription.kubectl, subscription.awscli = get_bin(subscription)

    def create_vive_software(self):
        # Create database
        try:
            self.sudo().write({'is_check_delete_instance': False})
            self.create_database()
        except Exception as e:
            _logger.info(str(e))

        # Create domain
        try:
            self.create_route_53_record()
        except Exception as e:
            _logger.info(str(e))

        # Create Odoo instance
        try:
            self.create_k8s_pod()
        except Exception as e:
            _logger.info(str(e))

    def get_k8s_env(self):
        user_email = self.partner_id.email
        user_password = self.partner_id.user_ids.get_password()
        user_name = self.partner_id.name
        user_phone = self.partner_id.phone
        user_company_name = self.partner_id.company_name
        user_country_id = self.partner_id.country_id.name
        user_zip = self.partner_id.zip
        user_street = self.partner_id.street
        user_lang = self.partner_id.lang

        mail_server = self.env['ir.mail_server'].search([('active', '=', True)], limit=1)
        mail_server_str = '|-|'.join(str(x) for x in [
            mail_server.smtp_host,
            mail_server.smtp_port,
            mail_server.smtp_encryption,
            mail_server.smtp_user,
            mail_server.smtp_pass,
        ])
        database_endpoint = self.env['ir.config_parameter'].sudo().get_param(
            'vsaas_subscription_aws_k8s.database_endpoint')
        access_key_id = self.env['ir.config_parameter'].sudo().get_param(
            'vsaas_subscription_aws_k8s.access_key_id')
        secret_key = self.env['ir.config_parameter'].sudo().get_param(
            'vsaas_subscription_aws_k8s.secret_key')
        aws_region = self.env['ir.config_parameter'].sudo().get_param(
            'vsaas_subscription_aws_k8s.aws_region')
        aws_s3_bucket_name = self.env['ir.config_parameter'].sudo().get_param(
            'vsaas_subscription_aws_k8s.aws_s3_bucket_name')
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        sub_info = self.get_subscription_information()
        allowed_modules = sub_info['allowed_modules']
        if allowed_modules:
            allowed_modules = "," + ",".join(allowed_modules)
        else:
            allowed_modules = " "
        k8s_envs = [
            '-e',
            r"'s/${CUSTOMER_NAME}/%s/g'" % self.code_lower,
            '-e',
            r"'s/${DB_HOST}/%s/g'" % database_endpoint,
            '-e',
            r"'s/${DB_PASSWORD}/%s/g'" % self.database_password,
            '-e',
            r"'s/${DB_USER}/%s/g'" % self.code_lower,
            '-e',
            r"'s/${SUBSCRIPTION_CODE}/%s/g'" % self.code_lower,
            '-e',
            r"'s/${DOMAIN_NAME}/%s/g'" % self.website,
            '-e',
            r"'s/${USER_EMAIL}/%s/g'" % user_email,
            '-e',
            r"'s/${USER_NAME}/%s/g'" % user_name,
            '-e',
            r"'s,${USER_PASS},%s,g'" % re.escape(user_password),
            '-e',
            r"'s/${USER_PHONE}/%s/g'" % user_phone,
            '-e',
            r"'s/${USER_COMPANY}/%s/g'" % user_company_name,
            '-e',
            r"'s/${USER_COUNTRY}/%s/g'" % user_country_id,
            '-e',
            r"'s/${USER_ZIP}/%s/g'" % user_zip,
            '-e',
            r"'s/${USER_STREET}/%s/g'" % user_street,
            '-e',
            r"'s/${USER_LANG}/%s/g'" % user_lang,
            '-e',
            r"'s/${SMTP_SERVER}/%s/g'" % mail_server_str,
            '-e',
            r"'s/${ACCESS_ID}/%s/g'" % access_key_id,
            '-e',
            r"'s/${SECRET_KEY}/%s/g'" % secret_key,
            '-e',
            r"'s/${BUCKET_NAME}/%s/g'" % aws_s3_bucket_name,
            '-e',
            r"'s/${REGION}/%s/g'" % aws_region,
            '-e',
            r"'s/${ADMIN_PASSWORD}/%s/g'" % self.admin_password,
            '-e',
            r"'s/${MODULES}/%s/g'" % allowed_modules,
            '-e',
            r"'s/${ALLOWED_ACTIVE_USERS}/%s/g'" % sub_info['allowed_active_users'],
            '-e',
            r"'s/${EXPIRATION_DATE}/%s/g'" % sub_info['expiration_date'],
            '-e',
            r"'s/${SUB_ID}/%s/g'" % self.id,
            '-e',
            r"'s/${SUB_UUID}/%s/g'" % self.uuid,
            '-e',
            r"'s,${BASE_URL},%s,g'" % re.escape(base_url),
        ]
        return k8s_envs

    def create_k8s_pod(self):
        admin_password = self.generate_random_password()
        self.write({'admin_password': admin_password})
        manifests = [
            "default-networkpolicy.yaml",
            "web-namespace.yaml",
            "web-secret.yaml",
            "web-deployment.yaml",
            "web-ingress.yaml",
            "web-service.yaml",
        ]
        env = os.environ.copy()
        aws_bin = self.awscli.strip("/aws")
        env['PATH'] = env["PATH"] + ":/%s" % aws_bin
        k8s_envs = self.get_k8s_env()
        for m in manifests:
            manifest_file_path = current_path + "/k8s/%s" % m
            command = ['sed'] + k8s_envs + [manifest_file_path, " | ", self.kubectl, "apply", "-f", "-"]
            execute_sys_command(' '.join(command), shell=True, env=env)

    def create_route_53_record(self):
        zone_id = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.route53_hosted_zone_id')
        elb_endpoint = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.elb_endpoint')
        config = {
            "Comment": "Create new record",
            "Changes": [
                {"Action": "CREATE",
                 "ResourceRecordSet":
                     {"Name": self.website,
                      "Type": "CNAME",
                      "TTL": TTL,
                      "ResourceRecords": [
                          {"Value": elb_endpoint}
                      ]
                    }
                 }
            ]
        }
        output, err = execute_sys_command([
            self.awscli,
            "route53",
            "change-resource-record-sets",
            "--hosted-zone-id",
            zone_id,
            "--change-batch",
            json.dumps(config)
        ])

    def create_alb(self):
        pass

    def get_database_credentials(self):
        master_db_user = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.database_user')
        master_db_password = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.database_password')
        database_endpoint = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.database_endpoint')
        database_fwd_port = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.database_fwd_port')
        master_database = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.master_database')
        return master_db_user, master_db_password, database_endpoint, database_fwd_port, master_database

    def create_database(self):
        db_password = self.database_password or self.generate_random_password()
        master_db_user, master_db_password, database_endpoint, database_fwd_port, master_database = self.get_database_credentials()
        env = os.environ.copy()
        env['PGPASSWORD'] = master_db_password
#         try:
        execute_sys_command([
            "psql",
            "-U",
            master_db_user,
            "-d",
            master_database,
            "-p",
            database_fwd_port,
            "-h",
            "localhost",
            "-c",
            "CREATE USER {username} WITH PASSWORD '{password}' CREATEDB LOGIN;".format(username=self.code_lower, password=db_password)
        ], env=env)
#         except Exception as e:
#             raise ValidationError(_("Failed to connect to the database, please check the configuration to AWS RDS"))
        env['PGPASSWORD'] = db_password
        execute_sys_command([
            "psql",
            "-U",
            self.code_lower,
            "-d",
            master_database,
            "-p",
            database_fwd_port,
            "-h",
            "localhost",
            "-c",
            "CREATE DATABASE {username} WITH OWNER '{username}'".format(username=self.code_lower)
        ], env=env)
        self.write({'database_password': db_password})

    def generate_random_password(self):
        return str(uuid.uuid4())

    def cleanup_vive_software(self):
        # Update self
        self.sudo().write({'is_check_delete_instance': True})
        # Delete k8s pod
        try:
            self.cleanup_k8s()
        except Exception as e:
            _logger.info(str(e))
        # Delete database
        try:
            self.cleanup_database()
        except Exception as e:
            _logger.info(str(e))
        # Remove domain record
        try:
            self.cleanup_route_53_record()
        except Exception as e:
            _logger.info(str(e))
        # Delete storage
        try:
            self.delete_s3_bucket()
        except Exception as e:
            _logger.info(str(e))
        #send Email
        try:
            self.send_email_remove_instance_sale_subscription()
        except Exception as e:
            _logger.info(str(e))
        # Delete storage

    def delete_s3_bucket(self):
        if self.code_lower:
            execute_sys_command([
                self.awscli,
                "s3",
                "rm",
                f"s3://vive-storage/{self.code_lower}/",
                "--recursive"
            ])


    def cleanup_database(self):
        master_db_user, master_db_password, database_endpoint, database_fwd_port, master_database = self.get_database_credentials()
        env = os.environ.copy()
        env['PGPASSWORD'] = self.database_password
        # try:
        execute_sys_command([
            "psql",
            "-U",
            self.code_lower,
            "-d",
            master_database,
            "-p",
            database_fwd_port,
            "-h",
            "localhost",
            "-c",
            "DROP DATABASE {username} WITH (FORCE)".format(username=self.code_lower)
        ], env=env)
        # except Exception as e:
        #     raise ValidationError(_("Failed to connect to the database, please check the configuration to AWS RDS"))

        env['PGPASSWORD'] = master_db_password
        execute_sys_command([
            "psql",
            "-U",
            master_db_user,
            "-p",
            database_fwd_port,
            "-d",
            master_database,
            "-h",
            "localhost",
            "-c",
            "DROP USER {username};".format(username=self.code_lower)
        ], env=env)

    def cleanup_k8s(self):
        env = os.environ.copy()
        aws_bin = self.awscli.strip("/aws")
        env['PATH'] = env["PATH"] + ":/%s" % aws_bin
        # Remove deployment, ingress, secret, service, ... within subscription's namespace
        execute_sys_command([
            self.kubectl,
            "delete",
            "all",
            "--all",
            "-n",
            self.code_lower
        ], env=env)

        # Remove deployment, ingress, secret, service, ... within subscription's namespace
        execute_sys_command([
            self.kubectl,
            "delete",
            "namespaces",
            self.code_lower
        ], env=env)

    def cleanup_route_53_record(self):
        zone_id = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.route53_hosted_zone_id')
        elb_endpoint = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.elb_endpoint')
        config = {
            "Comment": "Delete record for subscription: %s" % self.code_lower,
            "Changes": [
                {"Action": "DELETE",
                 "ResourceRecordSet":
                     {"Name": self.website,
                      "Type": "CNAME",
                      "TTL": TTL,
                      "ResourceRecords": [
                          {"Value": elb_endpoint}
                      ]
                      }
                 }
            ]
        }
        output, err = execute_sys_command([
            self.awscli,
            "route53",
            "change-resource-record-sets",
            "--hosted-zone-id",
            zone_id,
            "--change-batch",
            json.dumps(config)
        ])

    def send_email_expired_trial_databases(self, days):
        """Deleting the inactive or expired trial databases and sending email notifications to the customers
        """
        email_context = self.env.context.copy()

        # update context
        email_context.update({
            'days_trial': days
        })

        template = self.env.ref('onnet_custom_subscription.email_expired_database')
        id = template.sudo().send_mail(self.id)
        self.env['mail.mail'].sudo().search([('id', '=', id)]).send()

    def send_email_remove_instance_sale_subscription(self):
        """In manually removing the instances, after clicking on Delete Instances, we can have another
          popup wizard which says "Do you want to
          send a notification email to the customer?" and the user can select Yes or No before continuing
       """
        template = self.env.ref('onnet_custom_subscription.email_remove_instance_sale_subscription')
        id_email = template.sudo().send_mail(self.id)
        self.env['mail.mail'].sudo().search([('id', '=', id_email)]).send()

    def set_register_payment_manual(self):
        """ Register Payment"""
        try:
            self.check_confirm_payment = True
            invoice = self.create_invoice_vive_software()
            invoice.sudo().write({'other_payment': True})
        except Exception as e:
            _logger.info(str(e))

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': invoice.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def set_payment_manual(self):
        """ Email order """
        try:
            self.order_id._send_order_confirmation_mail()
            self.order_id.sudo().write({'state': 'sale'})
            self.set_active()
        except Exception as e:
            _logger.info(str(e))

        """ Email Active instance """
        try:
            self._send_email_active()
        except Exception as e:
            _logger.info(str(e))

        """ Email Active instance """
        try:
            default_template = self.env['ir.config_parameter'].sudo().get_param('sale.default_invoice_email_template')
            if not default_template:
                return
            self.id_email_sucess.message_post_with_template(int(default_template), email_layout_xmlid="mail.mail_notification_paynow")

        except Exception as e:
            _logger.info(str(e))