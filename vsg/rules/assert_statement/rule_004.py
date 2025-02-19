
from vsg.rules import split_line_at_token_when_between_tokens_unless_token_is_found

from vsg import token

lTokens = []
lTokens.append(token.assertion.severity_keyword)

oStart = token.assertion.keyword
oEnd = token.concurrent_assertion_statement.semicolon
oStop = token.assertion_statement.semicolon


class rule_004(split_line_at_token_when_between_tokens_unless_token_is_found):
    '''
    Checks the severity keyword is on its own line for concurrent assertion statements.
    '''

    def __init__(self):
        split_line_at_token_when_between_tokens_unless_token_is_found.__init__(self, 'assert', '004', lTokens, oStart, oEnd, oStop)
        self.solution = "Place **severity** keyword on its own line."
