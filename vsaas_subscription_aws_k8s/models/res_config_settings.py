from odoo import models, api, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    awscli_bin_path = fields.Char(string=_("AWS bin path"), config_parameter='vsaas_subscription_aws_k8s.aws_bin')
    kubectl_bin_path = fields.Char(string=_("Kubectl bin path"),
                                   config_parameter='vsaas_subscription_aws_k8s.kubectl_bin')
    route53_hosted_zone_id = fields.Char(string=_("Route 53 hosted zone ID"),
                                         config_parameter='vsaas_subscription_aws_k8s.route53_hosted_zone_id')
    elb_endpoint = fields.Char(string=_("ELB Endpoint"), config_parameter='vsaas_subscription_aws_k8s.elb_endpoint')
    database_endpoint = fields.Char(string=_("Database Endpoint"), config_parameter='vsaas_subscription_aws_k8s.database_endpoint')
    database_user = fields.Char(string=_("Database User"),
                                    config_parameter='vsaas_subscription_aws_k8s.database_user')
    database_password = fields.Char(string=_("Database Password"),
                                    config_parameter='vsaas_subscription_aws_k8s.database_password')
    database_fwd_port = fields.Char(string=_("Database Fwd Port"),
                                    config_parameter='vsaas_subscription_aws_k8s.database_fwd_port')
    master_database = fields.Char(string=_("Master Database"), config_parameter='vsaas_subscription_aws_k8s.master_database')

    aws_access_key_id = fields.Char(string=_("Access ID"), config_parameter='vsaas_subscription_aws_k8s.access_key_id')
    aws_secret_key = fields.Char(string=_("Secret key"), config_parameter='vsaas_subscription_aws_k8s.secret_key')
    aws_region = fields.Char(string=_("Region"), config_parameter='vsaas_subscription_aws_k8s.region')
    aws_s3_bucket_name = fields.Char(string=_("S3 Bucket Name"), config_parameter='vsaas_subscription_aws_k8s.s3_bucket', default='vive-storage')
