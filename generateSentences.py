import argparse
import json

from enum import Enum, auto
import re
from typing import List, Dict
from numpy import single
from pydantic import BaseModel

import random

class WordType(Enum):
    Question = auto()
    Pronoun = auto()
    Verb = auto()

class PronounName(str, Enum):
    I = "Я"
    You = "Ты"
    He = "Он"
    She = "Она"
    We = "Mы"
    YouPlural = "Вы"
    They = "Они"

class VerbQuestion(Enum):
    ToWhom = auto()
    Whom = auto()
    WithWhom = auto()

class SingleOrPlural(Enum):
    Singular = auto()
    Plural = auto()

class ConjugationType(Enum):
    Infinitive = 3
    First = 0
    Second = 1
    Third = 2

class WordForm(BaseModel):
    conjugationType: ConjugationType
    singleOrPlural: SingleOrPlural

class Word(BaseModel):
    type: WordType

class QuestionWord(Word):
    text: str

class PronounWord(Word):
    pronounName: PronounName

class Conjugation(BaseModel):
    singular: str
    plural: str

class VerbForms(BaseModel):
    infinitive: str
    conjugations: List[Conjugation]

class VerbWord(Word):
    forms: VerbForms
    expectInfinitive: bool
    questions: List[VerbQuestion]

class Words(BaseModel):
    questionWords: List[QuestionWord] = []
    pronouns: List[PronounWord] = []
    verbs: List[VerbWord] = []

def textLowercase(func):
    return lambda *args, **kwargs: func(*args, **kwargs).lower()

@textLowercase
def wordText(word: Word) -> str:
    match (word):
        case QuestionWord(text=text):
            return text
        case PronounWord(pronounName=pronounName):
            return pronounName.value
        case VerbWord(forms=forms):
            return forms.infinitive

def pronounForm(pronoun: PronounWord) -> WordForm:
    match(pronoun.pronounName):
        case PronounName.I:
            return WordForm(conjugationType=ConjugationType.First, singleOrPlural=SingleOrPlural.Singular)
        case PronounName.You:
            return WordForm(conjugationType=ConjugationType.Second, singleOrPlural=SingleOrPlural.Singular)
        case PronounName.He | PronounName.She:
            return WordForm(conjugationType=ConjugationType.Third, singleOrPlural=SingleOrPlural.Singular)
        case PronounName.We:
            return WordForm(conjugationType=ConjugationType.First, singleOrPlural=SingleOrPlural.Plural)
        case PronounName.YouPlural:
            return WordForm(conjugationType=ConjugationType.Second, singleOrPlural=SingleOrPlural.Plural)
        case PronounName.They:
            return WordForm(conjugationType=ConjugationType.Third, singleOrPlural=SingleOrPlural.Plural)

@textLowercase
def verbTextInForm(verb: VerbWord, form: WordForm) -> str:
    match(form.conjugationType):
        case ConjugationType.Infinitive:
            return verb.forms.infinitive
        case _:
            conjugation = verb.forms.conjugations[form.conjugationType.value]
            return conjugation.singular if form.singleOrPlural == SingleOrPlural.Singular else conjugation.plural

def makeWordsByText(words: Words) -> Dict[str, Word]:
    wordTextToWord = {}

    for wordList in [words.questionWords, words.pronouns, words.verbs]:
        for word in wordList:
            wordTextToWord[wordText(word)] = word
    return wordTextToWord

def randomWordFromList(wordList: List[Word]) -> Word:
    return wordList[random.randrange(0, len(wordList))]

def newOrAnyWord(wordList: List[Word], wordTextToWord: Dict[str, Word], wordsToLearn: List[str]) -> Word:
    type = wordList[0].type
    wordsToLearnOfType = [wordTextToWord[wordText] for wordText in wordsToLearn if wordTextToWord[wordText].type == type]
    if len(wordsToLearnOfType) > 0:
        return randomWordFromList(wordsToLearnOfType)
    return randomWordFromList(wordList)

def newOrAnyVerb(verbList: List[Word], wordTextToWord: Dict[str, Word], wordsToLearn: List[str]) -> Word:
    verbsToLearn = [wordTextToWord[wordText] for wordText in wordsToLearn if wordTextToWord[wordText].type == WordType.Verb]
    if len(verbsToLearn) > 0:
        if any([verb for verb in verbsToLearn if verb.expectInfinitive]) or bool(random.getrandbits(1)):
            return randomWordFromList(verbsToLearn)
        else:
            return randomWordFromList([verb for verb in verbList if verb.expectInfinitive])
    return randomWordFromList(verbList)

def newOrAnyNotExpectsInfinitiveVerb(verbList: List[VerbWord], wordTextToWord: Dict[str, Word], wordsToLearn: List[str]) -> VerbWord:
    verbsToLearn = [wordTextToWord[wordText] for wordText in wordsToLearn if wordTextToWord[wordText].type == WordType.Verb and not wordTextToWord[wordText].expectInfinitive]
    if len(verbsToLearn) > 0:
        return randomWordFromList(verbsToLearn)
    return randomWordFromList([verb for verb in verbList if not verb.expectInfinitive])

def generateSentence(words: Words, wordTextToWord: Dict[str, Word], wordsToLearn: List[str]):
    startWithQuestion = any(
        [wordTextToWord[wordText].type == WordType.Question for wordText in wordsToLearn]
    ) or bool(random.getrandbits(1))
    
    sentence = []

    if startWithQuestion:
        sentence.append(wordText(
            newOrAnyWord(words.questionWords, wordTextToWord, wordsToLearn)
        ))

    pronoun = newOrAnyWord(words.pronouns, wordTextToWord, wordsToLearn)
    sentence.append(wordText(pronoun))
    newVerb: VerbWord = newOrAnyVerb(words.verbs, wordTextToWord, wordsToLearn)
    sentence.append(verbTextInForm(newVerb, pronounForm(pronoun)))
    if (newVerb.expectInfinitive):
        sentence.append(wordText(
            newOrAnyNotExpectsInfinitiveVerb(words.verbs, wordTextToWord, wordsToLearn)
        ))

    sentence[0] = sentence[0].capitalize()
    return " ".join(sentence)

def parseAgrs():
    parser = argparse.ArgumentParser(description='generate sentences')
    parser.add_argument('--wordsConfig', help='path to config with words', type=str, required=True)    
    args = parser.parse_args()
    return args    

def main():
    args = parseAgrs()

    with open(args.wordsConfig, "rt") as f:
        config = json.load(f)

    words = Words()
    for questionWord in config["words"]["questionWords"]:
        words.questionWords.append(QuestionWord(type = WordType.Question, **questionWord))
    for pronounName in PronounName:
        words.pronouns.append(PronounWord(type = WordType.Pronoun, pronounName=pronounName))
    for verb in config["words"]["verbs"]:
        words.verbs.append(VerbWord(type = WordType.Verb, **verb))

    wordsToLearn: List[str] = config["wordsToLearn"]
    wordsToLearn = [word.lower() for word in wordsToLearn]
    wordTextToWord = makeWordsByText(words)

    sentence = generateSentence(
        words,
        wordTextToWord,
        random.sample(wordsToLearn, min(len(wordsToLearn), 2))
    )

    print(sentence)


if __name__ == "__main__":
    main()