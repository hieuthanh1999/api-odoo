import subprocess
import logging
import sys
import os
from odoo.exceptions import ValidationError

default_env = os.environ.copy()
_logger = logging.getLogger(__name__)


def get_bin(self):
    kubectl = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.kubectl_bin',
                                                               default='/usr/bin/kubectl')
    awscli = self.env['ir.config_parameter'].sudo().get_param('vsaas_subscription_aws_k8s.aws_bin',
                                                              default='/usr/bin/aws')
    return kubectl, awscli


def execute_sys_command(command, env=False, shell=False):
    """

    :param command: List of command and it's arguments
    :param env: Environment object
    :return:
    """
    if not env:
        env = default_env
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, shell=shell)
    stdout, stderr = p.communicate()

    if stdout:
        _logger.info(stdout.decode(sys.stdout.encoding).strip('\n'))
    if stderr:
        _logger.info(stderr.decode(sys.stdout.encoding).strip("\n"))
    return stdout, stderr
