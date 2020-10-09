# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from awscli.customizations.exceptions import ParamValidationError
from awscli.autoprompt.prompttoolkit import PromptToolkitPrompter


def validate_auto_prompt_args_are_mutually_exclusive(parsed_args, **kwargs):
    cli_auto_prompt = getattr(parsed_args, 'cli_auto_prompt', False)
    no_cli_auto_prompt = getattr(parsed_args, 'no_cli_auto_prompt', False)
    if cli_auto_prompt and no_cli_auto_prompt:
        raise ParamValidationError(
            'Both --cli-auto-prompt and --no-cli-auto-prompt cannot be '
            'specified at the same time.'
        )


class AutoPromptDriver:

    NO_PROMPT_ARGS = ['help', '--version']

    def __init__(self, session, prompter=None):
        self._prompter = prompter
        self._session = session

    def _should_autoprompt(self, parsed_args, args):
        # Order of precedence to check:
        # - check if any arg rom NO_PROMPT_ARGS in args
        # - check if '--no-cli-auto-prompt' was specified
        # - check if '--cli-auto-prompt' was specified
        # - check configuration chain
        if any(arg in args for arg in self.NO_PROMPT_ARGS):
            return False
        if getattr(parsed_args, 'no_cli_auto_prompt', False):
            return False
        if getattr(parsed_args, 'cli_auto_prompt', False):
            return True
        config = self._session.get_config_variable('cli_auto_prompt')
        return config.lower() == 'on'

    def auto_prompt_arguments(self, args, parsed_args, **kwargs):
        """Prompts the user for input while providing autoprompt support along
        the way.

        :type args: list
        :param args: The list of command line args entered at the command line
            just before entering into the autoprompt workflow.

        :type parsed_args: ``argparse.Namespace``
        :param parsed_args: The parsed options at the `aws` entrypoint. This is
            primarily used to check if the autoprompt override arguments
            ``--cli-auto-prompt`` or ``--no-cli-auto-prompt`` were specified.

        :rtype: list of strings
        :return: A list of the arguments that the user typed into the buffer
            (aka "construction zone").
            Example: ['ec2', 'describe-instances']

        """
        if self._should_autoprompt(parsed_args, args):
            args = self._prompter.prompt_for_values(args)
        return args


class AutoPrompter:
    """Fills out the arguments list by calling out to the UI prompt backend to
    do the actual prompting of arguments. This makes it easy to swap out
    the UI prompt backend easily if needed.

    """
    def __init__(self, completion_source, driver, prompter=None):
        self._completion_source = completion_source
        self._driver = driver
        if prompter is None:
            prompter = PromptToolkitPrompter(self._completion_source,
                                             self._driver)
        self._prompter = prompter

    def prompt_for_values(self, original_args):
        return self._prompter.prompt_for_args(original_args)
