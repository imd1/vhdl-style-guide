
from vsg.rules import token_case

from vsg import token

lTokens = []
lTokens.append(token.subprogram_body.is_keyword)


class rule_502(token_case):
    '''
    Checks the function is keyword has proper case.
    '''

    def __init__(self):
        token_case.__init__(self, 'function', '502', lTokens)
