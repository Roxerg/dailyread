
import re

def partial_word_capitalization(name):
    name = name.replace('`', '\'')

    for sep in ['\'', '`', '-']:
        split_word = name.split(sep)
        if len(split_word) != 1:
            name = sep.join(list(map(lambda x: x.capitalize(), split_word)))
    
    name = re.sub('^([mM][aA]?[Cc])([A-Za-z]+)', lambda x: x.group(1).capitalize() + x.group(2).capitalize(), name)

    return name

def process_author(name):
    name = ' '.join(list(map(lambda x: partial_word_capitalization(x.capitalize()), name.split(' '))))
    name = ' '.join(list(map(lambda x: x+"." if len(x) == 1 else x, name.split(' '))))

    return name

def capitalize_with_exceptions(word):
    exceptions = ['a', 'an', 'the', 'of', 'over', 'by', 'as', 'over']
    if not word in exceptions:
        return word.capitalize()
    else:
        return word

def process_title(title):
    title = ' '.join(list(map(lambda x: capitalize_with_exceptions(x), title.split(' '))))
    
    # capitalize the first word either way
    title_split = title.split(' ')
    title_split[0] = title_split[0].capitalize()
    title = ' '.join(title_split)
    print(title)




process_author("samwell oblin-garcia o'senior mctavishmc")
process_author("g r r martin")

process_title("the book of the good")