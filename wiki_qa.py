import re
import requests
import lxml.html
import sys
import rdflib

WRONG_Q_FORMAT = "The question you entered is not in the right format. Try one of the following formats:\n" + \
'\n'.join([
    '\tWho is the <relation> of the <entity>?',
    '\tWho is the <relation> of <entity>?',
    '\tWhat is the <relation> of the <entity>?',
    '\tWhat is the  <relation> <entity>?',
    '\tWhen was <entity> born?'
])

NO_ANSWER_FOUND = "Sorry, no answer was found. Try rephrasing your question."

patterns = [
    re.compile(r'^Who is the (.*) of the (.*)[?]$'),
    re.compile(r'^Who is the (.*) of (.*)[?]$'),
    re.compile(r'^What is the (.*) of the (.*)[?]$'),
    re.compile(r'^What is the (.*) of (.*)[?]$'),
    re.compile(r'^When was (.*) born[?]$')
    ]

stopwords = {'is','and','of','the','a',' '}

wiki_prefix = "https://en.wikipedia.org/wiki/"

def extract_relation_and_entity(question):
    """
    extract relations and entities from predefined patterns
    :param question: the string from which to extract the data
    :return: Tuple containing extracted relations and entities
    """
    for pattern in patterns:
        if pattern.match(question):
            return pattern.findall(question)[0]
    return None


def gen_sparql_query(var_name, entity, relation):
    """
    :param var_name: the name of the variable in the query
    :param relation: the name of the relation in the query
    :param entity: the name of the entity in the query
    :return: a sparql query based on tha variable, entity and relation
    """
    where_clause = "wiki:%s wiki:%s ?%s" % (entity, relation, var_name)
    query = "PREFIX wiki: <%s>\n" \
             "SELECT ?%s WHERE {\n" \
             "\t%s\n" \
             "}" % (wiki_prefix, var_name, where_clause)

    return query


def get_infobox_data(entity):
    url = wiki_prefix + entity
    infobox_xpath = "//table[contains(@class, 'infobox')]"

    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)

    relations = doc.xpath(infobox_xpath + '//th//text()')
    if len(relations) == 0:
        # no infobox data found
        return None
    res = {}
    relation_set = set()
    for relation in relations:
        if relation not in relation_set:
            relation_set.add(relation)
            values = get_relation_from_doc(doc, relation, duplicate=(relations.count(relation) > 1))
            if (values and len(values) > 0):
                res[relation] = values
    return res


def get_relation_from_doc(doc,relation,duplicate=False):
    infobox_xpath = "//table[contains(@class, 'infobox')]"

    answers = doc.xpath(
        infobox_xpath + '//th[.//text() = \'' +
        relation + '\' or .//a//text() = \'' +
        relation + '\']/../td//text()'
    )
    if len(answers) == 0:
        answers = doc.xpath(
            infobox_xpath + '//th[.//text() = \'' +
            relation + '\' or .//a//text() = \'' +
            relation + '\']/../td/a/text()'
        )
        if len(answers) == 0:
            answers = doc.xpath(
                infobox_xpath + '//th[contains(.//text(), \'' +
                relation + '\') or contains(.//a//text(), \'' +
                relation + '\')]/../td//text()'
            )
    if (relation == 'Capital'):
        answers = answers[0]
    if duplicate:
        delimiter = ', '
    else:
        delimiter = ''
    answer =  delimiter.join(answers)
    if relation == 'Born':
        # special case - consider the 'Born' field as a single string
        answer = answer.replace('\n',' ')
    return clean_answer(answer)


def clean_answer(s):
    # remove any brackets while possible
    while True:
        s_new = re.sub(r'([\(\[]).*?([\)\]])', r'', s)
        if s_new == s:
            break
        s = s_new
    # remove trailing spaces and special characters
    result = s.strip().replace(u'\xa0', u'_').strip('\n')
    if len(result)>0:
        return [str.strip(' ,') for str in re.split('\\n|\, ',result) if str.strip(' ,') != '' and str.strip(' ,') not in stopwords]
    return []

def build_ontology(entity_name, data):
    g = rdflib.Graph()
    entity = rdflib.URIRef(wiki_prefix + entity_name)
    for (relation, results) in data.items():
        relation = rdflib.URIRef(wiki_prefix + relation)
        for result_name in results:
            result = rdflib.URIRef(wiki_prefix + result_name)
            g.add((entity, relation, result))
    g.serialize("graph.nt", format="nt")
    return g



def prepare_entity(str):
    return str.strip(' ').replace(' ', '_')

def get_relation_variations(str):
    if str == '':
        return []
    variations = [
        str # add original string
    ]

    if (str.title() != str):
        variations.append(str.title())  # add title

    if (str.lower() != str):
        variations.append(str.lower())  # add lowercase

    words = str.split(' ')
    if len(words)>1:
        # add where only first letter in uppercase and the rest in lowercase
        word = '\xa0'.join([words[i].title() if i == 0 else words[i] for i in range(len(words))])
        variations.append(word)
    return variations


def get_answer(entity_name, relation_name):
    url = wiki_prefix + entity_name

    res = requests.get(url)
    doc = lxml.html.fromstring(res.content)

    variations = get_relation_variations(relation_name)
    for relation in variations:
        answers = get_relation_from_doc(doc, relation)
        if (answers):
            return ', '.join(answers)
    return NO_ANSWER_FOUND


if __name__ == '__main__':
    question = ' '.join(sys.argv[1:])

    res = extract_relation_and_entity(question)
    if res:
        if type(res) == str:
            entity = res
            relation = 'Born'
        else:
            entity = res[1]
            relation = res[0]

        #infobox_data = get_infobox_data(prepare_entity(entity))
        print(get_answer(entity,relation))

    else:
        print(WRONG_Q_FORMAT)

    # print(ent)
    # if type(ent) == str:
    #     print(gen_sparql_query('d',ent, "bornOn"))
    # else:
    #     print(gen_sparql_query('d', ent[1], ent[0]))

    # variations = get_relation_variations(res[0])
    # for relation in variations:
    #     answer = get_answer(entity, relation)
    #     if (answer):
    #         print(answer)
    #         sys.exit() # stop searching for answers
    # print(NO_ANSWER_FOUND)


