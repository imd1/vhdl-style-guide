
from vsg import parser
from vsg import token

from vsg.rules import consistent_token_case

lTokens = []
lTokens.append(token.procedure_specification.designator)

lIgnore = []
lIgnore.append(parser.whitespace)
lIgnore.append(parser.carriage_return)
lIgnore.append(parser.blank_line)


class rule_507(consistent_token_case):
    '''
    Checks capitalization consistency of procedure names.
    '''

    def __init__(self):
        consistent_token_case.__init__(self, 'procedure', '507', lTokens, lIgnore)
