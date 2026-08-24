"""Backward-compatible alias for fill_level_examples --level a1."""

from learning.management.commands.fill_level_examples import Command as FillLevelExamplesCommand


class Command(FillLevelExamplesCommand):
    help = 'Fill missing A1 example sentences (alias for fill_level_examples --level a1)'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(level='a1')
