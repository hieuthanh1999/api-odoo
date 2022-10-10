from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import subprocess, os
from ..helpers import get_bin, execute_sys_command


class AwsConfiguration(models.TransientModel):
    _name = 'aws.configuration'

    aws_access_key = fields.Char(string="Access Key", required=1)
    aws_secret_key = fields.Char(string="Secret Key", required=1)
    aws_region = fields.Char(string="Region", required=1)
    aws_output = fields.Char(string="Output Format", default="json")
    aws_k8s_cluster_name = fields.Char(string="K8s cluster name", required=1)

    @api.model
    def get_bin(self):
        kubectl = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.kubectl_bin',
                                                                   default='/usr/bin/kubectl')
        awscli = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.aws_bin',
                                                                  default='/usr/bin/aws')
        return kubectl, awscli

    @api.model
    def execute_sys_command(self, command):
        """

        :param command:
        :return:
        """
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr and p.errors:
            raise ValidationError(stderr)

    def aws_register(self):
        kubectl, awscli = self.get_bin()
        profile = {
            'aws_access_key_id': self.aws_access_key,
            'aws_secret_access_key': self.aws_secret_key,
            'region': self.aws_region,
            'output': self.aws_output,
        }

        self.env['ir.config_parameter'].set_param('vsaas_subscription_aws_k8s.access_key_id', self.aws_access_key)
        self.env['ir.config_parameter'].set_param('vsaas_subscription_aws_k8s.secret_key', self.aws_secret_key)
        self.env['ir.config_parameter'].set_param('vsaas_subscription_aws_k8s.region', self.aws_region)

        for p in profile:
            execute_sys_command([
                awscli,
                "configure",
                'set',
                p,
                profile[p]

            ])
        execute_sys_command([
            awscli,
            "eks",
            "--region",
            self.aws_region,
            "update-kubeconfig",
            "--name",
            self.aws_k8s_cluster_name
        ])