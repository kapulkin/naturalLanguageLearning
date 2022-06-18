# Natural language learning

Sentense generator to learn a new language by translating sentences from native language to target language.

## Requirements

Python 3.10

## How to use

Idea is to learn new words step by step.

1. Create a config file and fill it with words you already know.
2. Add words you want to learn to the config and highlight them in config.
3. Now run the generator, it will generate sentenses with 2 new words and other known to you.

```
python3.10 generateSentences.py --wordsConfig config.json
```

4. As new words are learned, remove the hghlighting for them in config and repeat the process.