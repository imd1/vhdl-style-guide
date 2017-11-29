
from vsg.rules.variable_assignment import variable_assignment_rule
from vsg import check
from vsg import fix


class rule_004(variable_assignment_rule):
    '''Variable assignment rule 004 ensures the alignment of multiline variable_assignment statements.'''

    def __init__(self):
        variable_assignment_rule.__init__(self)
        self.identifier = '004'
        self.solution = 'Align with space after the ":=" keyword.'
        self.phase = 5

    def analyze(self, oFile):
        for iLineNumber, oLine in enumerate(oFile.lines):
            if oLine.isVariableAssignment and oLine.isVariableAssignmentEnd:
                continue
            if oLine.isVariableAssignment:
                iAlignmentColumn = oLine.line.find(':=') + len(':= ')
                continue
            if oLine.insideVariableAssignment and not oLine.isComment:
                check.multiline_alignment(self, iAlignmentColumn, oLine, iLineNumber)

    def _fix_violations(self, oFile):
        for iLineNumber in self.dFix['violations']:
            fix.multiline_alignment(self, oFile, iLineNumber)
