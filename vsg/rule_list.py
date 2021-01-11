
import os
import importlib
import inspect

from . import junit
from . import report
from . import utils
from . import severity


def get_python_modules_from_directory(sDirectoryName, lModules):
    '''
    Returns a list of files with an extension of py from a directory.
    It ignores files starting with a double underscore __.

    Parameters:

      sDirectoryName (string)

    Modifies:

      lModules (string list)
    '''
    try:
        lDirectoryContents = os.listdir(sDirectoryName)
        for sFileName in lDirectoryContents:
            if sFileName.endswith('.py') and not sFileName.startswith('__'):
                lModules.append(sFileName.replace('.py', ''))
    except OSError:
        print('ERROR: specified local rules directory ' + sDirectoryName + ' could not be found.')
        exit()


def get_rules_from_module(lModules, lRules):
    '''
    Returns a list of files that start with "rule_".

    Parameters:

      lModules (list)

    Modifies:

      lRules (object list)
    '''
    for sModuleName in lModules:
        for name, obj in inspect.getmembers(importlib.import_module(sModuleName)):
            if name.startswith('rule_') and name != 'rule_item':
                lRules.append(obj())


def load_local_rules(sDirectoryName):
    '''
    Loads rules from the directory passed to this routine.

    Parameters:

      sDirectoryName (string)

    Returns: (string list)
    '''
    lLocalModules = []
    get_python_modules_from_directory(sDirectoryName, lLocalModules)
    lRules = []
    get_rules_from_module(lLocalModules, lRules)
    return lRules


def load_rules():
    '''
    Loads rules from the vsg/rules directory.

    Parameters:  None

    Returns:  (rule object list)
    '''
    lRules = []
    for name, oPackage in inspect.getmembers(importlib.import_module('vsg.rules')):
        if inspect.ismodule(oPackage):
            for name, oRule in inspect.getmembers(oPackage):
                if inspect.isclass(oRule) and name.startswith('rule_'):
                    lRules.append(oRule())

    return lRules


def maximum_phase(lRules):
    '''
    Determines the maximum phase number from all the rules.

    Parameters:
      lRules (rule object list)

    Returns: (integer)
    '''
    maximumPhaseNumber = 0
    for oRule in lRules:
        if oRule.phase > maximumPhaseNumber:
            maximumPhaseNumber = oRule.phase
    return maximumPhaseNumber


class rule_list():
    '''
    Contains a list of all rules to be checked.
    It loads all base rules.
    Localized rules are loaded if specified.

    Parameters:

      oVhdlFile: (vhdlFile object)

      oSeverityList: (severity list object)

      sLocalRulesDirectory: (string) (optional)
    '''
    def __init__(self, oVhdlFile, oSeverityList, sLocalRulesDirectory=None):
        self.rules = load_rules()
        if sLocalRulesDirectory:
            self.rules.extend(load_local_rules(sLocalRulesDirectory))
        self.iNumberRulesRan = 0
        self.lastPhaseRan = 0
        self.oVhdlFile = oVhdlFile
        self.maximumPhase = maximum_phase(self.rules)
        self.violations = False
        self.oSeverityList = oSeverityList

    def fix(self, iFixPhase=7, lSkipPhase=[], dFixOnly=None):
        '''
        Applies fixes to all violations found.

        Parameters:

          iFixPhase : (integer)

          lSkipPhases : (list of integers)

          dFixOnly : (fix list dictionary)
        '''
        for phase in range(1, int(iFixPhase) + 1):
            if phase in lSkipPhase:
                if phase == 1:
                    self.oVhdlFile.set_token_indent()
                continue

            for subphase in range(1, 5):
                lRules = self.get_rules_in_phase(phase)
                lRules = self.get_rules_in_subphase(lRules, subphase)
                lRules = filter_out_disabled_rules(lRules)
                for oRule in lRules:
                    if oRule.severity.type == severity.error_type:
                        oRule.fix(self.oVhdlFile, dFixOnly)
                    else:
                        oRule.analyze(self.oVhdlFile)

            if phase == 1:
                self.oVhdlFile.fix_blank_lines()

    def get_rules_in_phase(self, iPhaseNumber):
        '''
        Returns a list of rules in a given phase.

        Parameters:

          iPhaseNumber : (integer)

        Returns: (list of rule objects)
        '''
        lReturn = []
        for oRule in self.rules:
            if oRule.phase == iPhaseNumber:
                lReturn.append(oRule)
        return lReturn

    def get_rules_in_subphase(self, lRules, iSubPhase):
        '''
        Returns a list of rules in a given subphase.

        Parameters:

          lRules : (list of rule objects)

          iSubPhase : (integer)

        Returns: (list of rule objects)
        '''
        lReturn = []
        for oRule in lRules:
            if oRule.subphase == iSubPhase:
                lReturn.append(oRule)
        return lReturn

    def check_rules(self, bAllPhases=False, lSkipPhase=[]):
        '''
        Analyzes all rules in increasing phase order.
        If there is a violation in a phase, analysis is halted.

        Parameters:

            bAllPhases : (boolean)
            lSkipPhase : (list of integers)
        '''
        self.iNumberRulesRan = 0
        iFailures = 0
        self.violations = False
        for phase in range(1, 8):
            if phase in lSkipPhase:
                continue

            for subphase in range(1, 5):
                lRules = self.get_rules_in_phase(phase)
                lRules = self.get_rules_in_subphase(lRules, subphase)
                lRules = filter_out_disabled_rules(lRules)

                for oRule in lRules:
                    oRule.analyze(self.oVhdlFile)
                    if oRule.severity.type == severity.error_type:
                        iFailures += len(oRule.violations)
                    self.iNumberRulesRan += 1
                self.lastPhaseRan = phase
                if iFailures > 0 and not bAllPhases:
                    self.violations = True
                    break
            else:
                continue
            break

    def report_violations(self, sOutputFormat):
        '''
        Prints out violations to stdout.

        Parameters:

          sOutputFormat (string)
        '''
#        print('--> report_violations')
        dRunInfo = {}
        dRunInfo['filename'] = self.oVhdlFile.filename
        dRunInfo['stopPhase'] = 7
        dRunInfo['violations'] = []

        for iLineNumber in range(0, self.oVhdlFile.get_line_count() + 1):
            for oRule in self.rules:
                if oRule.has_violations():
                    lViolations = oRule.get_violations_at_linenumber(iLineNumber)
#                    print(f'{oRule.name}_{oRule.identifier} | {iLineNumber} | {len(lViolations)}')
                    dRunInfo['violations'].extend(lViolations)

        dRunInfo['stopPhase'] = self.lastPhaseRan
        dRunInfo['num_rules_checked'] = self.get_number_of_rules_ran()
        dRunInfo['total_violations'] = len(dRunInfo['violations'])
        dRunInfo['maxSeverityNameLength'] = self.oSeverityList.iMaxNameLength
        dRunInfo['severities'] = {}

        for oSeverity in self.oSeverityList.get_severities():
            dRunInfo['severities'][oSeverity.name] = oSeverity.count
#        print(dRunInfo)
        if sOutputFormat == 'vsg':
            report.vsg_stdout.print_output(dRunInfo)
        elif sOutputFormat == 'syntastic':
            report.syntastic_stdout.print_output(dRunInfo)
        else:
            report.summary_stdout.print_output(dRunInfo)

    def configure(self, configurationFile):
        '''
        Configures individual rules based on dictionary passed.

        Parameters:

          configurationFile: (dictionary)
        '''
        if configurationFile and 'rule' in configurationFile:
            self._validate_configuration_rule_exists(configurationFile)
            for oRule in self.rules:
                oRule.configure(configurationFile)
        if configurationFile['debug']:
            for oRule in self.rules:
                oRule.set_debug()

    def _validate_configuration_rule_exists(self, configurationFile):
        '''
        Validates rules called out in the configuration files exist in the rule set.

        If a rule does not exist then:

          1) an error message will be printed
          2) tool will exit with a status of 1

        Parameters:

          configurationFile: (dictionary)

        Returns:  nothing
        '''
        lRuleNames = []
        for oRule in self.rules:
            lRuleNames.append(oRule.name + '_' + oRule.identifier)
        for sRule in configurationFile['rule']:
            if not sRule == 'global' and sRule not in lRuleNames:
                print('ERROR: Rule ' + sRule + ' referenced in configuration could not be found')
                exit(1)

    def extract_junit_testcase(self, sVhdlFileName):
        '''
        Creates JUnit XML file listing all violations found.

        Parameters:

          sVhdlFileName (string)

        Returns: (junit testcase object)
        '''
        oTestcase = junit.testcase(sVhdlFileName, str(0), 'failure')
        oFailure = junit.failure('Failure')
        for oRule in self.rules:
            if len(oRule.violations) > 0 and oRule.severity.type == severity.error_type:
                for dViolation in oRule.violations:
                    sLine = oRule.name + '_' + oRule.identifier + ': '
                    sLine += str(utils.get_violation_line_number(dViolation)) + ' : '
                    sLine += dViolation.get_solution()
                    oFailure.add_text(sLine)
        oTestcase.add_failure(oFailure)

        return oTestcase

    def extract_violation_dictionary(self):
        '''
        Creates a dictionary of violations which were found.

        Returns: (dictionary)
        '''
        dReturn = {}
        dReturn['violations'] = []
        for oRule in self.rules:
            if oRule.has_violations:
                for oViolation in oRule.violations:
                    dTemp = {}
                    dTemp['rule'] = oRule.unique_id
                    dTemp['linenumber'] = oViolation.get_line_number()
                    dTemp['solution'] = oViolation.get_solution()
                    dReturn['violations'].append(dTemp)
        return dReturn

    def get_configuration(self):
        '''
        Returns a dictionary with every rule and how it is configured.

        Parameters:

          None

        Returns: (dictionary)
        '''
        dConfiguration = {}
        for oRule in self.rules:
            sId = oRule.name + '_' + oRule.identifier
            dConfiguration[sId] = oRule.get_configuration()
        return dConfiguration

    def clear_violations(self):
        for oRule in self.rules:
            oRule.clear_violations()

    def get_number_of_rules_ran(self):
        return self.iNumberRulesRan


def filter_out_disabled_rules(lRules):
    '''
    Removes rules which are disabled from a list of rule objects.

    Parameters:

      lRules : (list of rule objects)

    Returns: (list of rule objects)
    '''
    lReturn = []
    for oRule in lRules:
        if not oRule.disable:
            lReturn.append(oRule)
    return lReturn
