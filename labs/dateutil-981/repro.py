from dateutil.parser import parse, ParserError

try:
    parse('0-100')
except ParserError:
    print('ParserError, as documented')
