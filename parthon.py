import inspect

#try:
#    from itertools import tee, count    
#except:
#     def count(n=0):
#         while True:
#             yield n
#             n += 1
#     
#     def tee(iterable):
#         def gen(next, data={}, cnt=[0]):
#             for i in count():
#                 if i == cnt[0]:
#                     item = data[i] = next()
#                     cnt[0] += 1
#                 else:
#                     item = data.pop(i)
#                 yield item
#         it = iter(iterable)
#         return (gen(it.next), gen(it.next))

class ParseError(Exception):
    def __init__(self, state, code, msg):
        self._state = state
        self._code = code
        self._msg = msg

class Input: 
    def __init__(self, data, source=None):
        self._data = data
        if source is None:
            self._position = 0            
            self._line = 0
            self._col = 0
        else:
            self._position = source._position
            self._line = source._line
            self._col = source._col

    def readChar(self):
        raise NotImplementedError        
        
    def next(self):
        c = self.readChar()
        if c == "\n":
            self._line += 1
            self._col = 0
        else:
            self._col += 1
        return c

    def tee(self):
        clone = self.__class__(self._data, self)
        return self, clone
                
class StringInput(Input):
    def readChar(self):
        try:
            c = self._data[self._position]          
        except:
             raise StopIteration
        self._position += 1
        return c

class FileInput(Input):
    def readChar(self):
        self.data.seek(self._postion)
        c = self._data.read()          
        if c == "":
            raise StopIteration
        self._position += 1
        return c
        
class IterableInput(Input):
    def tee(self):
        import itertools
        return itertools.tee(self._data)

    def readChar(self):
        return self._data.next()
        
        
def tee(anInput):
    return anInput.tee()
                 
def parse(parser, data):
    if isinstance(data, Input):
        theInput = data
    elif type(data) is str:
        theInput = StringInput(data)
    elif type(data) is file:
        theInput = FileInput(data)
    else:
        theInput = IterableInput(data)

    def iterResult():
      try :
        for res, data2, dictVars  in parser.run(theInput, {}):
          if res:
            yield res, data2, dictVars
      except ParseError, e:
        print "ParseError(%s) : "%(e._code)
        print "  - line %s col %s"%(e._state._line, e._state._col)
        print "  - Error %s - %s"%(e._code, e._msg)  
        
    return iterResult()    
             
def func_name(fct):
    try:
        return fct.func_name
    except AttributeError:
        pass
    try:
        return fct.__name__
    except AttributeError:
        return "**unknown**"

class Result:
    pass
             
class ResultOK(Result):
    def __init__(self, value, *args):
        self.value = value
        self.args = args

    def getValue(self):
        return self.value        
        
    def __nonzero__(self):
        return True
    
    def __repr__(self):
        return "ResultOK(%s)" % repr(self.value)
                                  
class ResultFail(Result):
    def __init__(self, *args):
        self.args = args
    
    def __nonzero__(self):
        return False

    def __repr__(self):
        return "ResultFail()"

#class State:
#    def __init__(self, flux, dictVars):
#        self.flux = flux
#        self.dictVars = dictVars
#    
#    def getDictVars(self):
#        return self.dictVars
#        
#    def dup(self):        
#        self.flux, newFlux = tee(self.flux)
#        return State(newFlux, self.dictVars)
        
class Parser:
    def __init__(self, children, characteristics):
        self.setChildren(children)
        if characteristics is None: 
            self._characteristics = []
        else:
            self._characteristics = characteristics
            
    def setChildren(self, children):              
        if children is None:
            self._children = []
        else:
            self._children = children
        if len(self._children) == 1:
            self._parser = children[0]
        else:
            self._parser = None
        
    def getChildren(self, total=False):  
        return self._children
    
    def assign(self, nomVar):
        return AssignParser(self, nomVar)
    
    def disjonction(self, other):
        return DisjonctionParser([self, other])

    def rdisjonction(self, other):
        return DisjonctionParser([other, self])
    
    def conjonction(self, other):
        return ConjonctionParser([self, other])

    def rconjonction(self, other):
        return ConjonctionParser([other, self])

    def conjonctionSpaces(self, separator, other):
        return ConjonctionParser([separator, other]).rconjonction(self)
    
    def argsParser(self, fct):
        return ArgsParser(self, fct)
    
    def function(self, func):
        return FunctionParser(self, func)
    
    def __or__(self, other):
        return self.disjonction(other)       
        
    def __ror__(self, other):
        return self.rdisjonction(other)       

    def __sub__(self, other):
        return self.conjonctionSpaces(optSpacesParser, other)
    
    def __add__(self, other):
        return self.conjonctionSpaces(manySpacesParser, other)

    def __div__(self, fct):
        return self.argsParser(fct)
                            
    def __ge__(self, func):
        return self.function(func)
    
    def __rshift__(self, other):
        return self.conjonction(other)

    def __rrshift__(self, other):
        return self.rconjonction(other)
    
    def __getitem__(self, nomVar):
        return self.assign(nomVar)
    
    def __call__(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)
#        data, dataTmp = tee(data)
#        print "run %s on '%s' (%s)"%(repr(self), "".join(list(dataTmp)), #dictVars)
#        for res in self.run(data, dictVars):
#            yield res
#       yield ResultFail() 
        
    def run(self, data, dictVars):
        raise NotImplementedError
    
    def asTree(self, indent=0):
        strTmp = "| "*indent+"+"+self.__class__.__name__+" : "+self.getCharacteristicsFormatted()+"\n"
        for parser in self.getChildren(total=False):
            strTmp += parser.asTree(indent+1)
        return strTmp

    def asTree2(self, indent=0):
        strTmp = "| "*indent+"+"+repr(self)+"\n"
        for parser in self.getChildren(total=False):
            strTmp += parser.asTree2(indent+1)
        return strTmp
        
    def toParser(p):
        if type(p) == str:
            if len(p) == 1:
                return lit(p)
            return txt(p)
        return p
    toParser = staticmethod(toParser)

    def getCharacteristicsFormatted(self):
        return repr(self.getCharacteristics())
        
    def getCharacteristics(self):
        return self._characteristics
    
    def getParser(self):
        return self        
        
    def asText(self):
        return repr(self)
            
    def __repr__(self):
        characteristics = ", ".join(repr(c) for c in self.getCharacteristics())
        if self._parser is None:
            return "%s(%s)"%(self.__class__, characteristics)
        else:
            return "%s(%s, %s)"%(self.__class__, self._parser, characteristics)

class CharParser(Parser):
    def __init__(self):
        Parser.__init__(self, [], [])

    def run(self, data, dictVars):
        try:
            res = data.next()
        except StopIteration:
            yield ResultFail(), data, dictVars
        else:    
            yield ResultOK(res), data, dictVars                

class ConstParser(Parser):
    def __init__(self, value=None):
        Parser.__init__(self, [], [value])
        self.value = value
    
    def run(self, data, dictVars):
        yield ResultOK(self.value), data, dictVars
        
class AssignParser(Parser):
    def __init__(self, parser, nomVar):
        Parser.__init__(self, [parser], [nomVar])
        self.nomVar = nomVar
    
    def run(self, data, dictVars):
        for res, data, _ in self._parser.run(data, {}):
            if res:
                dictVars[self.nomVar] = res.getValue()
            yield res, data, dictVars

    def asText(self):
        return "(%s)[%s]"%(self._parser.asText(), repr(self.nomVar))

class ComposableParser(Parser):        
    def __init__(self, lstParsers):
        Parser.__init__(self, lstParsers, [])        
                        
    def addChild(self, parser):
        self._children.append(parser)        
            
    def setChildren(self, newChildren):
        self._children = []
        for p in newChildren:
            self.addChild(Parser.toParser(p))

    def __repr__(self):
        children = ", ".join(repr(c) for c in self.getChildren())
        return "%s(%s)"%(self.__class__, children)
                
class ConjonctionParser(ComposableParser):
        
    def conjonction(self, other):
        if other.__class__ == ConjonctionParser:
            self._children += other._children
        else:
            self.addChild(other)
        return self

    def rconjonction(self, other):
        if other.__class__ == ConjonctionParser:
            other._children += self._children
            return other
        self._children.insert(0, other)
        return self
                    
    def run(self, data, dictVars, numParser=0):
       if numParser == len(self._children):
           yield ResultOK([]), data, dictVars
       else:
           parser = self._children[numParser]
           for item, data2, dictVars in parser.run(data, dictVars):
               if item:
                   itemValue = item.getValue()
                   for rest, data3, dictVars in self.run(data2, dictVars, numParser+1):
                       if rest:
                           rest.getValue().insert(0, itemValue)    
                           yield rest, data3, dictVars
           yield ResultFail(), data, dictVars           
                         
#    def conjonction(self, other):
#        self.lstParsers.append(other)
#        return self

#    def conjonctionSpaces(self, separator, other):
#        self.lstParsers.append(separator)
#        self.lstParsers.append(other)
#        return self
    
#    def __repr__(self):
#        return "ConjonctionParser(%s)"%(self.lstParsers)

    def asText(self):
        return " >> ".join(["(%s)"%(p.asText()) for p in self.getChildren()])       

                    
class DisjonctionParser(ComposableParser):
    
    def run(self, data, dictVars):
        data, dataSave = tee(data)
        for parser in self._children:
            data, data2 = tee(data)
            for res, data3, _ in parser.run(data2, {}):
                if res: 
                    yield res, data3, dictVars
        yield ResultFail(), dataSave, dictVars
                
#    def __repr__(self):
#        return "DisjonctionParser(%s)"%(self.lstParsers)

    def asText(self):
        return " | ".join(["(%s)"%(p.asText()) for p in self.getChildren()])       
        
                            
class FunctionParser(Parser):
    def __init__(self, parser, function):          
        Parser.__init__(self, [parser], [function])
        self.function = function
        self.inspectData = inspect.getargspec(function)
            
    def run(self, data, dictVars):
        data, dataSave = tee(data)
        for res, data2, dictVars2 in self._parser.run(data, {}):
            if not res:
                continue
            funcArgs, varArgs, varkw, defaults = self.inspectData
            if varkw is not None:
                dictArgs = dictVars
            else:
                dictArgs = {}
                for var in funcArgs:
                    try:
                        dictArgs[var] = dictVars2[var]
                    except KeyError:
                        pass
            yield ResultOK(self.function(**dictArgs)), data2, dictVars
        yield ResultFail(), dataSave, dictVars
    
    def __repr__(self):
        return "FunctionParser(%s, %s)"%(self._parser, func_name(self.function))

    def asText(self):
        return "(%s) >= %s"%(self._parser.asText(), func_name(self.function))
        
        
class ArgsParser(Parser):
    def __init__(self, parser, function):          
        Parser.__init__(self, [parser], [function])
        self.function = function
        self.inspectData = inspect.getargspec(function)        
    
    def run(self, data, dictVars):
        data, dataSave = tee(data)
        for res, data2, dictVars2 in self._parser.run(data, {}):
#            dataSave, data = tee(dataSave)
            if not res:
                continue
            funcArgs, varArgs, varkw, defaults = self.inspectData
        
#             if varkw:
#                 dictArgs = dictVars2        
#             else:            
            dictArgs = {}
            for var in funcArgs:
                try:
                    dictArgs[var] = dictVars2[var]
                except KeyError:
                    pass
            parser = self.function(**dictArgs)
            for res, data2, dictVars3 in parser.run(data2, dictVars):
                yield res, data2, dictVars
        yield ResultFail(), dataSave, dictVars
    
    def __repr__(self):
        return "ArgsParser(%s, %s)"%(self._parser, func_name(self.function))

    def asText(self):
        return "%s / %s"%(self._parser.asText(), func_name(self.function))        

        
class SatParser(Parser):
    def isTrue(self, x):
        return x        
    
    def __init__(self, parser, function=None):
        Parser.__init__(self, [parser], [self.function])
        self.function = function or self.isTrue    
            
    def test(self, x):
        if self.function(x.getValue()):
            return x
        return ResultFail()
    
    def run(self, data, dictVars):
        data, dataSave = tee(data)
        for res, data2, _  in self._parser.run(data, {}):
            if not res:
                yield ResultFail(), data2, dictVars
            else:
                yield self.test(res), data2, dictVars

    def asText(self):
        return "sat(%s, %s)"%(self.parser.asText(), func_name(self.function))        
        
        
# class NegSatParser(SatParser):
#     def test(self, x):
#         if self.function(x.getValue()):
#             return ResultFail()
#         return x

class FailureParser(Parser):
    def __init__(self, parser, value=None):
        Parser.__init__(self, [parser], [value])
        self.value  = None
        
    def run(self, data, dictVars):
        data, dataSave = tee(data)
        for res, data2, _  in self._parser.run(data, {}):
            if res:
                yield ResultFail(), data2, dictVars
            else:
                yield ResultOK(self.value), data2, dictVars

class ErrorParser(Parser):
    def __init__(self, code=1, msg="error"):                
        Parser.__init__(self, [], [code, msg])
        self._code = code
        self._msg = msg

    def run(self, data, dictVars):
        raise ParseError(data, self._code, self._msg)
                
class ManyParser(Parser):
    def __init__(self, parser, constructor, init, atLeastOne=False, maximum=False):
        Parser.__init__(self, [parser], [constructor, init, atLeastOne, maximum])
        self.constructor = constructor
        self.init = init
        self.atLeastOne = atLeastOne
        self.maximum = maximum
        
    def run(self, data, dictVars):
        for res in self.runBis(data, dictVars, self.atLeastOne, self.maximum):
            yield res
        
    def runBis(self, data, dictVars, atLeastOne=False, maximum=False):
        res = self.init
        data, saveData = tee(data)
        listePossibles = [(ResultOK(res), saveData, dictVars)]
        noItem = True
        for item, data, _ in self._parser.run(data, {}):
            if item:
                noItem = False
                for rest, data2, _ in self.runBis(data, {}, False, maximum):
                    if rest:
                        res = self.constructor(item.getValue(), rest.getValue())
                        yield ResultOK(res), data2, dictVars
        if noItem:
            if atLeastOne:
                yield ResultFail(), saveData, dictVars
            else:
                yield ResultOK(self.init), saveData, dictVars
        elif not maximum:
                yield ResultOK(self.init), saveData, dictVars                         

                
class NamedParser(Parser):
    def __init__(self, parserName):
        Parser.__init__(self, [], [parserName])
        self.parserName = parserName                         
                                                                        
    def run(self, data, dictVars):
        try:
            for r in self._parser.run(data, dictVars):
                yield r
        except NameError:
            print "The parser: '%s' is not defined"%self.parserName
        
        
class FctParser(Parser):
    def __init__(self, fctName, args=[], kwargs={}):
        Parser.__init__(self, [], [fctName, args, kwargs])
        self.fctName = fctName                         
        self.args = args
        self.kwargs = kwargs
                                                                        
    def run(self, data, dictVars):
        try:
            parser = self.fctName(*self.args, **self.kwargs)
            for r in parser.run(data, dictVars):
                yield r
        except NameError, e:
            print e
            print "The parser: '%s' is not defined"%self.fctName
                    
            
class SubParser(Parser):
    def __init__(self, lstParsers=None, lstCharacteristics=None):
        Parser.__init__(self, lstParsers, lstCharacteristics)
        self._result = None

        
    def getChildren(self, total=False):
        if total:
            return [self.getParser()]
        return []
        
    def getParser(self):
        raise NotImplementedError
    
    def getResult(self, value):
        return self._result
    
    def run(self, data, dictVars):
        parser = self.getParser()
        data, dataSave = tee(data)
        for res, data2, _  in parser.run(data, {}):
            if res:
                result = self.getResult(res.getValue())
                yield ResultOK(result), data2, dictVars
        yield ResultFail(), dataSave, dictVars
 
        
class LitParser(SubParser):                
    def __init__(self, txt, res=None):
        SubParser.__init__(self, [], [txt, res])
        self._txt = txt
        if res is not None:
            self._result = res
        else:
            self._result = txt

    def getParser(self):
        def eq(x): 
            return x==self._txt
        return sat (eq)

    def __repr__(self):
        return "%s"%(repr(self._txt))
        
        
class TextParser(LitParser):                

    def getParser(self):
        if len(self._txt) == 0:
            return nothing
        if len(self._txt) == 1:
            return lit(self._txt)
        return ConjonctionParser([lit(c) for c in self._txt])
              
class EndOfTextParser(SubParser):
    def getParser(self):
        return fail(item)

    def __repr__(self):
        return "eot"

class OptSpacesParser(SubParser):
    def getParser(self):
        return manyChars0(space)

    def __repr__(self):
        return "optSpaces"
                    
class ManySpacesParser(SubParser):
    def getParser(self):
        return manyChars(space)

    def __repr__(self):
        return "manySpaces"
                              
def debug(a):
    print '-------------'+repr(a)
    return a

item  = CharParser()

nothing = ConstParser()
    
def fail(p, val=None):
    return FailureParser(p, val)

endOfText = eot = EndOfTextParser()

def satParser(p, fct=None):
    return SatParser(p, fct)

def negSatParser(p, fct): 
    return NegSatParser(p, fct)

def namedParser(parserName): 
    return NamedParser(parserName)

def sat(fct): 
    return SatParser(item, fct)
    
def negsat(fct): 
    return NegSatParser(item, fct)
    
def many(parser, constructor, init): 
    return ManyParser(parser, constructor, init, atLeastOne=True)

def many0(parser, constructor, init):
    return ManyParser(parser, constructor, init)

def maxi(parser, constructor, init): 
    return ManyParser(parser, constructor, init, atLeastOne=True, maximum=True)

def maxi0(parser, constructor, init):
    return ManyParser(parser, constructor, init, maximum=True)

def lit(c): 
    return LitParser(c)        
#def lit(c): 
#    def eq(x):
#        return x==c
#    return sat (eq)

def notLit(c):
    def neq(x):
        return x != c
    return sat (neq)

def notInList(l):
    def isNotInList(x):
        return x not in l
    return sat(isNotInList)
      
    
def inList(l):
    def isInList(x):
        return x in l
    return sat(isInList)

digit = sat(str.isdigit)
lower = sat(str.islower)
upper = sat(str.isupper)

def txt(theWord, res=None):
    return TextParser(theWord, res)
##def txt(theWord, res=None):
##    def fct():
##        if res != None: return res
##        else:           return theWord
##    return ConjonctionParser([lit(c) for c in theWord]) >= fct

# def testInList(x, lst):
#     if x in lst:
#         return x
#     return None
        
dot    = lit('.')
at     = lit('@')
plus   = lit("+")
minus  = lit("-")
div    = lit("/")
mul    = lit("*")
symbList = "#|!/?.:;,"
symb  = inList(symbList)

letter = sat(str.isalpha)#lower | upper
alphanum = sat(str.isalnum)#letter | digit
character = alphanum | symb

def iden(a):
    return a

def brack(a, p, b): 
    return a >> p["a"] >> b >= iden

space = lit(' ') | lit('\n')
      
def cnsWord(w, l): 
    return w+l

def manyChars(parser): 
    return many(parser, cnsWord, '')

def manyChars0(parser): 
    return many0(parser, cnsWord, '')

def maxiChars(parser): 
    return maxi(parser, cnsWord, '')

def maxiChars0(parser): 
    return maxi0(parser, cnsWord, '')

words = manyChars(letter)
words0 = manyChars0(letter)

word = maxiChars(letter)
word0 = maxiChars0(letter)

def convert(fct):
    def f(x):
        return fct(x)
    return f

number = maxiChars(digit)["x"] >= convert(int)

manySpacesParser = manySpaces = ManySpacesParser() #manyChars(space)
optSpacesParser  = optSpaces  = OptSpacesParser()  #manyChars0(space)

error = ErrorParser()

def mark(m=None):
    def f(a):
        if m != None:
            return ((m, a),)
        else:
            return (a,)
    return f

def concat2(a, b):
    return a+b

def concat3(a, b, c):
    return a+b+c

def marked(p, v=None):
    return (p["a"] >= mark(v))

def seq(p, pSep):
    m = many0(pSep >> marked(p["a"]), concat2, ())
    return marked(p)["a"] >> m["b"] >= concat2

def seq2(p, pSep, fct, init):
    m = many0(pSep["op"] >> p["a"], fct, init)
    return p["a"] >> m["b"] >= fct