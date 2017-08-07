# Development

## Status and Contribution



## Run Tests

If you plan to debug or contribute, install to run directly from the source:

	$ python setup.py develop
	$ python setup.py test


## How to Contribute

Work in a virtual environment. I recommend to use [pipenv](https://github.com/kennethreitz/pipenv)
to make this easy.
Create and active the virtual environment:
```
$ cd /path/fabulist
$ pipenv shell
$ pip install -r requirements-dev.txt
$ python setup.py test
$ python setup.py develop
$ python setup.py sphinx
```

Make a release:
```
$ python setup.py test
$ python setup.py sdist bdist_wheel
$ twine upload
```


## Data Model and File Format

### Word List Entries

Word lists are represented as `_WordList` class instance which have a `key_list` attibute.
 consist of entry dictionaries:
```py
{"lemma":}
```


### Word List Files

Empty lines and lines starting with '#' are ignored.
Attributes are comma separated. Multi-value attributes are separated by '|'.
Attributes should be omitted if they can be generated using standard rules (e.g. plural of 'cat' is 'cats').
An attribute value of '-' can be used to prevent this value (e.g. 'blood' has no plural form).

Example:
```
# Noun list
# lemma | plural | tags
blood,-,
cat,,animal|pet
...
```

### Lorem Ipsum Files

TODO
