# encoding: utf8
from unittest import TestCase

from alex.components.slu.dainnclassifier import DAINNClassifier

from alex.components.slu.base import CategoryLabelDatabase, SLUPreprocessing
from alex.components.asr.utterance import Utterance, UtteranceNBList
from alex.components.slu.da import DialogueAct, DialogueActItem


class TestDAINNClassifier(TestCase):
    def test_parse_X(self):
        cldb = CategoryLabelDatabase()
        class db:
            database = {
                "task": {
                    "find_connection": ["najít spojení", "najít spoj", "zjistit spojení",
                                        "zjistit spoj", "hledám spojení", 'spojení', 'spoj',
                                       ],
                    "find_platform": ["najít nástupiště", "zjistit nástupiště", ],
                    'weather': ['pocasi', 'jak bude', ],
                },
                "number": {
                    "1": ["jednu"]
                },
                "time": {
                    "now": ["nyní", "teď", "teďka", "hned", "nejbližší", "v tuto chvíli", "co nejdřív"],
                },
            }
        print 'x'
        cldb.load(db_mod=db)

        preprocessing = SLUPreprocessing(cldb)
        import theano
        theano.config.floatX = 'float32'
        clf = DAINNClassifier(cldb, preprocessing, features_size=4)

        # Train a simple classifier.
        das = {
            '1': DialogueAct('inform(task=weather)'),
            '2': DialogueAct('inform(time=now)'),
            '3': DialogueAct('inform(task=weather)'),
            '4': DialogueAct('inform(task=connection)'),
        }
        utterances = {
            '1': Utterance('pocasi pocasi pocasi pocasi pocasi'),
            '2': Utterance('hned ted nyni hned ted nyni'),
            '3': Utterance('jak bude jak bude jak bude jak bude'),
            '4': Utterance('kdy a odkat mi to jede'),
        }
        clf.extract_classifiers(das, utterances, verbose=True)
        clf.prune_classifiers(min_classifier_count=0)
        clf.print_classifiers()
        clf.gen_classifiers_data(min_pos_feature_count=0,
                                 min_neg_feature_count=0,
                                 verbose2 = True)

        clf.train(inverse_regularisation=1e1, verbose=True)

        # Parse some sentences.
        utterance_list = UtteranceNBList()
        utterance_list.add(0.7, Utterance('pocasi'))
        utterance_list.add(0.7, Utterance('jak bude pocasi'))
        utterance_list.add(0.2, Utterance('hned'))
        utterance_list.add(0.2, Utterance('hned'))
        da_confnet = clf.parse_X(utterance_list, verbose=True)

        self.assertTrue(da_confnet.get_prob(DialogueActItem(dai='inform(task=weather)')) != 0.0)
        self.assertTrue(da_confnet.get_prob(DialogueActItem(dai='inform(time=now)')) != 0.0)