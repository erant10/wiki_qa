## Question Answering
### Final excercise for Web Data Management Course

The script generates a sparql query from a question written in natural language in one of the following formats:
- Who is the ``<relation>`` of the ``<entity>``?
- Who is the ``<relation>`` of ``<entity>``?
- What is the ``<relation>`` of the ``<entity>``?
- What is the  ``<relation>`` of ``<entity>``?
- When was ``<entity>`` born?

The answer to the question (from wikipedia) is printed to the console as output.
In addition, an `ontology.nt` file is created based on all of the additional information found the the "infobox" of the relevant wiki page

### running
```{console}
  python wiki_qa.py <natural language question string>
```

