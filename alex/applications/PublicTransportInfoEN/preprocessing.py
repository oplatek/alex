#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008.

from __future__ import unicode_literals

import re

from alex.components.slu.base import SLUPreprocessing
from alex.components.nlg.template import TemplateNLGPreprocessing
from alex.components.nlg.tools.en import word_for_number


class PTIENSLUPreprocessing(SLUPreprocessing):
    """
    Extends SLUPreprocessing for some transformations specific for Czech:
        - devocalisation of prepositions
        (- stemming).

    """
    def __init__(self, *args, **kwargs):
        super(PTIENSLUPreprocessing, self).__init__(*args, **kwargs)

        num_norms = []
        for num in xrange(60):
            num_norms.append(([unicode(num)], [word_for_number(num)]))
        self.text_normalization_mapping += num_norms

        self.text_normalization_mapping += [
            (["i'm"], ['i am']),
            (["it'll"], ['it will']),
            (["i'll"], ['i will']),
            # (['ze'], ['z']),
            # # (['se'], ['s']), # do not use this, FJ
            # (['barandov'], ['barrandov']),
            # (['litňanská'], ['letňanská']),
            # (['ípé', 'pa', 'pavlova'], ['i', 'p', 'pavlova']),
            # (['í', 'pé', 'pa', 'pavlova'], ['i', 'p', 'pavlova']),
            # (['čaplinovo'], ['chaplinovo']),
            # (['čaplinova'], ['chaplinova']),
            # (['zologická'], ['zoologická']),
        ]

    def normalise_utterance(self, utterance):
        utterance = super(PTIENSLUPreprocessing, self).normalise_utterance(utterance)
        #utterance = Utterance(" ".join(map(cz_stem, utterance)))
        return utterance



class PTIENNLGPreprocessing(TemplateNLGPreprocessing):
    """Template NLG preprocessing routines for Czech public transport information.

    This serves for spelling out relative and absolute time expressions,
    as well as translating certain slot values into Czech.
    """

    def __init__(self, ontology):
        super(PTIENNLGPreprocessing, self).__init__(ontology)
        # keep track of relative and absolute time slots
        self.rel_time_slots = set()
        self.abs_time_slots = set()
        # keep track of temperature and temperature interval slots
        self.temp_slots = set()
        self.temp_int_slots = set()
        # keep track of translated slots
        self.translated_slots = set()
        self.translations = {}
        # load their lists from the ontology
        if 'slot_attributes' in self.ontology:
            for slot in self.ontology['slot_attributes']:
                if 'relative_time' in self.ontology['slot_attributes'][slot]:
                    self.rel_time_slots.add(slot)
                elif 'absolute_time' in self.ontology['slot_attributes'][slot]:
                    self.abs_time_slots.add(slot)
                elif 'temperature' in self.ontology['slot_attributes'][slot]:
                    self.temp_slots.add(slot)
                elif 'temperature_int' in self.ontology['slot_attributes'][slot]:
                    self.temp_int_slots.add(slot)
        # load translations from the ontology
        if 'value_translation' in self.ontology:
            self.translations = self.ontology['value_translation']
            for slot in self.ontology['value_translation']:
                self.translated_slots.add(slot)

    def preprocess(self, template, svs_dict):
        """Preprocess values to be filled into an NLG template.
        Spells out temperature and time expressions and translates some of the values
        to English.

        :param svs_dict: Slot-value dictionary
        :return: The same dictionary, with modified values
        """
        # regular changes to slot values
        for slot, val in svs_dict.iteritems():
            # spell out time expressions
            if slot in self.rel_time_slots:
                svs_dict[slot] = self.spell_time(val, relative=True)
            elif slot in self.abs_time_slots:
                svs_dict[slot] = self.spell_time(val, relative=False)
            # spell out temperature expressions
            elif slot in self.temp_slots:
                svs_dict[slot] = self.spell_temperature(val, interval=False)
            elif slot in self.temp_int_slots:
                svs_dict[slot] = self.spell_temperature(val, interval=True)
            # translate some slot values (default to untranslated)
            elif slot in self.translated_slots:
                svs_dict[slot] = self.translations[slot].get(val, val)
        # reflect changes to slot values stored in the template
        slot_modif = {}

        def store_repl(match):
            slot, modif = match.groups()
            slot_modif[slot] = modif
            return '{' + slot + '}'

        template = re.sub(r'\{([^}/]+)/([^}]+)\}', store_repl, template)

        for slot, modif in slot_modif.iteritems():
            if modif == 'Cap1':
                svs_dict[slot] = svs_dict[slot][0].upper() + svs_dict[slot][1:]
        return template, svs_dict

    def spell_time(self, time, relative):
        """\
        Convert a time expression into words (assuming accusative).

        :param time: The 24hr numerical time value in a string, e.g. '8:05'
        :param relative: If true, time is interpreted as relative, i.e. \
                0:15 will generate '15 minutes' and not '0 hours and \
                15 minutes'.
        :return: time string with all numerals written out as words
        """
        if ':' not in time:  # 'now' and similar
            return time
        hours, mins = map(int, time.split(':'))
        time_str = []
        if not (relative and hours == 0):
            hr_id = 'hours'
            hours = word_for_number(hours)
            time_str.extend((hours, hr_id))
        if mins == 0 and (not relative or hours != 0):
            return ' '.join(time_str)
        if time_str:
            time_str.append('a')
        min_id = 'minutes'
        mins = word_for_number(mins)
        return ' '.join(time_str + [mins, min_id])

    def spell_temperature(self, value, interval):
        """Convert a temperature expression into words (assuming nominative).

        :param value: Temperature value (whole number in degrees as string), \
                e.g. '1' or '-10'.
        :param interval: Boolean indicating whether to treat this as a start \
                of an interval, i.e. omit the degrees word.
        :return: Czech temperature expression as string
        """
        ret = ''
        value = int(value)
        if value < 0:
            ret += 'minus '
            value = abs(value)
        ret += word_for_number(value)
        if not interval:
            ret += ' degrees'
        return ret