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
      import time
      context = ExecutionContext()
      try :
        t0 = time.time()
        for res, data2, context in parser.run(theInput, context):
          if res:
            t1 = time.time()
            print "Parsing time in seconds:", t1-t0
            yield res, data2, context
            t0 = time.time()
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
        return self.value is not Failure
    
    def __repr__(self):
        return "ResultOK(%s)" % repr(self.value)
                                  
class ResultFail(Result):
    def __init__(self, *args):
        self.args = args
    
    def __nonzero__(self):
        return False

    def __repr__(self):
        return "ResultFail()"

class NoResult:
    def __repr__(self):
        return "NoResult"
NoResult = NoResult()

class Default:
    def __repr__(self):
        return "Default"
Default = Default()

class Failure:
    def __repr__(self):
        return "Failure"
Failure = Failure()


class ExecutionContext:
    def __init__(self, context=None):
        self._dictVars = {}
        if context is not None:
            self._parsers = context._parsers
            return
        self.setDefaultParsers()
        
    def setDefaultParsers(self):   
        self._parsers = {}
        self._parsers["space"] = ~(lit(' ') | lit('\n'))
        self._parsers["comment"] = ~(nothing)
        
    def __getitem__(self, k):
        return self._dictVars[k]        

    def __setitem__(self, k, v):
        self._dictVars[k] = v        
                        
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
    
    def disjonction(self, other):
        return DisjonctionParser([self, other])

    def rdisjonction(self, other):
        return DisjonctionParser([other, self])
    
    def conjonction(self, other):
        return ConjonctionParser([self, other])

    def rconjonction(self, other):
        return ConjonctionParser([other, self])

    def conjonctionSeparated(self, separator, other):
        return ConjonctionParser([self, separator, other])
    
    def argsParser(self, fct):
        return ArgsParser(self, fct)
    
    def function(self, func):
        return FunctionParser(self, func)
    
    def assign(self, nomVar):
        return AssignParser(self, nomVar)

    def filter(self):
        return FilterParser(self)   
     
    __or__ = disjonction
    __ror__ = rdisjonction
    __div__ = argsParser 
    __ge__ = function
    __rshift__ = conjonction
    __rrshift__ = rconjonction
    __getitem__ = assign            
    __invert__ = filter

    def __sub__(self, other):
        return self.conjonctionSeparated(OptSpacesParser(), other)
    
    def __add__(self, other):
        return self.conjonctionSeparated(ManySpacesParser(), other)
    
    def __call__(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)
#        data, dataTmp = tee(data)
#        print "run %s on '%s' (%s)"%(repr(self), "".join(list(dataTmp)), #dictVars)
#        for res in self.run(data, dictVars):
#            yield res
#       yield ResultFail() 
        
    def runInSelfContext(self, data, content):
        subContext = ExecutionContext()
        for res, data, _ in self.run(data, subContext):
            yield res, data, _

    def run(self, data, context):
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

    def simplify(self):
        newChildren = []
        for child in self.getChildren():
            newChildren.append(child.simplify())            
        self.setChildren(newChildren)
        return self
                        
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

    def run(self, data, context):
        try:
            res = data.next()
        except StopIteration:
            yield ResultFail(), data, context
        else:    
            yield ResultOK(res), data, context                

class ConstParser(Parser):
    def __init__(self, value=NoResult):
        Parser.__init__(self, [], [value])
        self.value = value
    
    def run(self, data, context):
        yield ResultOK(self.value), data, context
        
class AssignParser(Parser):
    def __init__(self, parser, nomVar):
        Parser.__init__(self, [parser], [nomVar])
        self.nomVar = nomVar
    
    def run(self, data, context):
        subContext = ExecutionContext()
        for res, data, _ in self._parser.runInSelfContext(data, context):
            if res:
                context[self.nomVar] = res.getValue()
            yield res, data, context

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

    def simplify(self):            
        parserType = self.__class__
        oldChildren = self.getChildren(True)
        newChildren = []
        while oldChildren:
            child = oldChildren.pop(0)
            childType = child.__class__
            if childType == parserType:
                oldChildren = child.getChildren(True) + oldChildren
                continue
            newChildren.append(child.simplify())
        self.setChildren(newChildren)        
        return self
        
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
                    
    def run(self, data, context, numParser=0):
       if numParser == len(self._children):
           yield ResultOK([]), data, context
       else:
           parser = self._children[numParser]
           for item, data2, context in parser.run(data, context):
               if item:
                   itemValue = item.getValue()
                   for rest, data3, context in self.run(data2, context, numParser+1):
                       if rest:
                           if itemValue is not NoResult:
                                rest.getValue().insert(0, itemValue)    
                           yield rest, data3, context
           yield ResultFail(), data, context           
                         
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
    
    def run(self, data, context):
        data, dataSave = tee(data)
        for parser in self._children:
            data, data2 = tee(data)
            for res, data3, _ in parser.runInSelfContext(data2, context):
                if res: 
                    yield res, data3, context
        yield ResultFail(), dataSave, context
                
#    def __repr__(self):
#        return "DisjonctionParser(%s)"%(self.lstParsers)

    def asText(self):
        return " | ".join(["(%s)"%(p.asText()) for p in self.getChildren()])       
        
                            
class FunctionParser(Parser):
    def __init__(self, parser, function):          
        Parser.__init__(self, [parser], [function])
        self.function = function
        self.inspectData = inspect.getargspec(function)
            
    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, context2 in self._parser.runInSelfContext(data, context):
            if not res:
                continue
            funcArgs, varArgs, varkw, defaults = self.inspectData
            if varkw is not None:
                dictArgs = context._dictVars
            else:
                dictArgs = {}
                for var in funcArgs:
                    try:
                        dictArgs[var] = context2[var]
                    except KeyError:
                        pass
            yield ResultOK(self.function(**dictArgs)), data2, context
        yield ResultFail(), dataSave, context
    
    def __repr__(self):
        return "FunctionParser(%s, %s)"%(self._parser, func_name(self.function))

    def asText(self):
        return "(%s) >= %s"%(self._parser.asText(), func_name(self.function))
        
        
class ArgsParser(Parser):
    def __init__(self, parser, function):          
        Parser.__init__(self, [parser], [function])
        self.function = function
        self.inspectData = inspect.getargspec(function)        
    
    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, context2 in self._parser.runInSelfContext(data, context):
            if not res:
                continue
            funcArgs, varArgs, varkw, defaults = self.inspectData
            dictArgs = {}
            for var in funcArgs:
                try:
                    dictArgs[var] = context2[var]
                except KeyError:
                    pass
            parser = self.function(**dictArgs)
            for res, data2, context3 in parser.run(data2, context):
                yield res, data2, context
        yield ResultFail(), dataSave, context
    
    def __repr__(self):
        return "ArgsParser(%s, %s)"%(self._parser, func_name(self.function))

    def asText(self):
        return "%s / %s"%(self._parser.asText(), func_name(self.function))        

        
class SatParser(Parser):
    def __init__(self, parser, function=None):
        def isTrue(x):
            return x        
        self.function = function or isTrue    
        Parser.__init__(self, [parser], [self.function])
            
    def test(self, x):
        if self.function(x.getValue()):
            return x
        return ResultFail()
    
    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, _  in self._parser.runInSelfContext(data, context):
            if not res:
                yield ResultFail(), data2, context
            else:
                yield self.test(res), data2, context

    def asText(self):
        return "satParser(%s, %s)"%(self.parser.asText(), func_name(self.function))        
        
    def __repr__(self):
        return "SatParser(%s, %s)"%(self._parser, func_name(self.function))

class ConvertParser(Parser):
    def __init__(self, parser, function):
        self.function = function 
        Parser.__init__(self, [parser], [self.function])

    def convert(self, res):
        result = self.function(res.getValue())
        return ResultOK(result)

    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, _  in self._parser.runInSelfContext(data, context):
            if not res:
                yield ResultFail(), data2, context
            else:
                yield self.convert(res), data2, context

    def asText(self):
        return "ConvertParser(%s, %s)"%(self.parser.asText(), func_name(self.function))

    def __repr__(self):
        return "ConvertParser(%s, %s)"%(self._parser, func_name(self.function))

        
# class NegSatParser(SatParser):
#     def test(self, x):
#         if self.function(x.getValue()):
#             return ResultFail()
#         return x

class FailureParser(Parser):
    def __init__(self, parser, value=NoResult):
        Parser.__init__(self, [parser], [value])
        self.value = value
        
    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, _  in self._parser.runInSelfContext(data, context):
            if res:
                yield ResultFail(), data2, context
            else:
                yield ResultOK(self.value), data2, context

class ErrorParser(Parser):
    def __init__(self, code=1, msg="error"):                
        Parser.__init__(self, [], [code, msg])
        self._code = code
        self._msg = msg

    def run(self, data, context):
        raise ParseError(data, self._code, self._msg)
                
        
class ManyParser(Parser):
    def __init__(self, parser, constructor, init, atLeastOne=False, maximum=False):
        Parser.__init__(self, [parser], [constructor, init, atLeastOne, maximum])
        self.constructor = constructor
        self.init = init
        self.atLeastOne = atLeastOne
        self.maximum = maximum
        
    def run(self, data, context):
        for res in self.runBis(data, context, self.atLeastOne, self.maximum):
       #     print res
            yield res
    
    def runBis(self, data, context, _, __):
        res = self.init
        data, saveData = tee(data)
        listResults = []
        if not self.atLeastOne:
            listResults.append((ResultOK(res), saveData, context))
        listStates = [(res, data)]
        #print "---------------------"
        while listStates:
            res, data = listStates.pop()
            for item, data2, _ in self._parser.runInSelfContext(data, context):
                if item:
                    data, dataRes = tee(data2)
                    if item.getValue() is not NoResult:
                        res2 = self.constructor(res, item.getValue())   
                    else:
                        res2 = res 
                    #print "::>> (%s)(%s)"%(res2, item)
                    listStates.append((res2, data))                
                    listResults.append((ResultOK(res2), dataRes, context))
                
        if not listResults:
            yield ResultFail(), saveData, context
        else:
            if self.maximum:
                yield listResults[-1]
            else:
                for x in reversed(listResults):
                    yield x      


    def runBis__(self, data, context, atLeastOne=False, maximum=False):
        res = self.init
        data, saveData = tee(data)
        listePossibles = [(ResultOK(res), saveData, context)]
        noItem = True
        for item, data, _ in self._parser.runInSelfContext(data, context):
            if item:
                noItem = False
                for rest, data2, _ in self.runBis(data, ExecutionContext(), False, maximum):
                    if rest:
                        if item.getValue() is not NoResult:
                            res = self.constructor(rest.getValue(), item.getValue())
                        else: 
                            res = rest.getValue()
                        yield ResultOK(res), data2, context
        if noItem:
            if atLeastOne:
                yield ResultFail(), saveData, context
            else:
                yield ResultOK(self.init), saveData, context
        elif not maximum:
                yield ResultOK(self.init), saveData, context

                
class NamedParser(Parser):
    def __init__(self, parserName):
        Parser.__init__(self, [], [parserName])
        self._parserName = parserName                         
                                                                        
    def run(self, data, context):
        try:
            parser = vars()[self._parserName]
            for r in parser.run(data, context):
                yield r
        except NameError:
            print "The parser: '%s' is not defined"%self._parserName

class ContextualParser(Parser):
    def __init__(self, parserName):                
        Parser.__init__(self, [], [parserName])
        self._parserName = parserName

    def getChildren(self, total=False):
        if total:
            return [context._parsers[self._parserName]]
        return []

    def run(self, data, context):
        try:
            parser = context._parsers[self._parserName]
            for r in parser.run(data, context):
                yield r
        except KeyError:
            print "The parser: '%s' is not defined"%self._parserName
                
            
class FctParser(Parser):
    def __init__(self, fctName, args=[], kwargs={}):
        Parser.__init__(self, [], [fctName, args, kwargs])
        self.fctName = fctName                         
        self.args = args
        self.kwargs = kwargs
                                                                        
    def run(self, data, context):
        try:
            parser = self.fctName(*self.args, **self.kwargs)
            for r in parser.run(data, context):
                yield r
        except NameError, e:
            print e
            print "The parser: '%s' is not defined"%self.fctName

            
class FutureCheckerParser(Parser):
    def __init__(self, parser, result=NoResult):
        Parser.__init__(self, [parser], [result])
        self._result = result
    
    def run(self, data, context):
        #parser = self.getParser(context)
        data, dataSave = tee(data)
        for res, _, _ in self._parser.runInSelfContext(data, context):
            if res:
                yield ResultOK(self._result), dataSave, context
                break
        yield ResultFail(), dataSave, context

class NoFutureCheckerParser(Parser):
    def __init__(self, parser, result=NoResult):
        Parser.__init__(self, [parser], [result])
        self._result = result
    
    def run(self, data, context):
        #parser = self.getParser(context)
        data, dataSave = tee(data)
        for res, _, _ in self._parser.runInSelfContext(data, context):
            if res:
                yield ResultFail(), dataSave, context
                break
        yield ResultOK(self._result), dataSave, context

class FilterParser(Parser):
    def __init__(self, parser):
        Parser.__init__(self, [parser], [])
           
    def run(self, data, context):
        data, dataSave = tee(data)
        for res, data2, _ in self._parser.runInSelfContext(data, context):
            if res:
                yield ResultOK(NoResult), data2, context
                break
        yield ResultFail(), dataSave, context


class FlowReplacementParser(Parser):
    def __init__(self, parser):
        Parser.__init__(self, [parser], [])
    
    def run(self, data, context):
        parser = self.getParser()        
        
            
class SubParser(Parser):
    def __init__(self, lstParsers=None, lstCharacteristics=None):
        Parser.__init__(self, lstParsers, lstCharacteristics)
        self._result = None
        
    def getChildren(self, total=False):
        if total:
            return [self.getParser()]
        return []
        
    def getParser(self, context):
        raise NotImplementedError
    
    def getResult(self, value, context):
        return self._result
    
    def run(self, data, context):
        parser = self.getParser(context)
        data, dataSave = tee(data)
        for res, data2, _  in parser.runInSelfContext(data, context):
            if res:
                result = self.getResult(res.getValue(), context)
                yield ResultOK(result), data2, context
        yield ResultFail(), dataSave, context
 
        
class LitParser(SubParser):                
    def __init__(self, txt, res=Default):
        SubParser.__init__(self, [], [txt, res])
        self._txt = txt
        if res is not Default:
            self._result = res
        else:
            self._result = txt

    def getParser(self, context):
        def eq(x): 
            return x==self._txt
        return sat (eq)

    def __repr__(self):
        return repr(self._txt)
        
        
class TextParser(LitParser):                
    def getParser(self, context):
        if len(self._txt) == 0:
            return nothing
        if len(self._txt) == 1:
            return LitParser(self._txt)
        return ConjonctionParser([LitParser(c) for c in self._txt])
              
class EndOfTextParser(SubParser):
    def getParser(self, context):
        return FailureParser(item, NoResult)

    def __repr__(self):
        return "eot"

class OptSpacesParser(SubParser):
    def getParser(self, context):
        return manyChars0(context._parsers["space"])

    def __repr__(self):
        return "optSpaces"
                    
class ManySpacesParser(SubParser):
    def getParser(self, context):
        return manyChars(context._parsers["space"])

    def __repr__(self):
        return "manySpaces"

class NothingParser(SubParser):        
    def __init__(self, res=None):
        SubParser.__init__(self, [], [res])
        self._result = res

    def getParser(self, context):
        return ConstParser(self._result)

    def __repr__(self):
        return "nothing"
                                                
def debug(a):
    print '-------------'+repr(a)
    return a

item  = CharParser()

nothing = NothingParser()
    
def fail(p, val=NoResult):
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

def txt(theWord, res=Default):
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
      
def cnsWord(word, char): 
    return word+char

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

manySpaces = ManySpacesParser()#ContextualParser("manySpaces") #manyChars(space)
optSpaces  = OptSpacesParser()#ContextualParser("optSpaces")  #manyChars0(space)

def optSpaced(parser):
  return optSpaces >> parser >> optSpaces


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
