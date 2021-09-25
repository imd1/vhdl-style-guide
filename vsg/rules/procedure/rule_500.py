
from vsg.rules import token_case

from vsg import token

lTokens = []
lTokens.append(token.procedure_specification.procedure_keyword)


class rule_500(token_case):
    '''
    Checks the procedure keyword has proper case.
    '''

    def __init__(self):
        token_case.__init__(self, 'procedure', '500', lTokens)
