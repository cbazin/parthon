from parthon import *
import UserList       
 
class ListElem2:#(UserList.UserList):
    
    def __init__(self):
        self._elem = None
        self._rest = None
        self._nbElems = 0

    def cloneAndAppend(self, newElem):
        newList = ListElem()
        newList._elem = newElem
        newList._rest = self
        newList._nbElems = self._nbElems + 1
        return newList

    def __iter__(self):
        current = self
        while current._rest is not None:
            yield current._elem
            current = current._rest 

    def __len__(self):
        return self._nbElems
    
    def __getitem__(self, i):
        if i < 0: 
            i = self._nbElems - i 
        for j, elem in self:
            if j == i: 
                return elem
        raise Exception("index out of range")

    def __repr__(self):
        return "<<"+ str(list(self)) +">>"

class ListElem(UserList.UserList):
    def __init__(self):
        self._root = self
        self._elem = None
        self._prevs = None
        self._nbElems = 0
        self._lst = None

    def cloneAndAppend(self, newElem):
        newList = ListElem()
        newList._elem = newElem
        newList._prevs = self
        newList._root = self._root
        newList._nbElems = self._nbElems + 1
        return newList

    def asList(self):
        if self._lst is None:
            current = self
            lst = []
            while current._prevs is not None:
                lst.append(current._elem)
                current = current._prevs
            lst.reverse()
            self._lst = lst
        return self._lst

    def __iter__(self):
        return iter(self.asList())

    def __len__(self):
        return self._nbElems
    
    def __getitem__(self, i):
        return self.asList()[i]

    def __repr__(self):
        return "<<"+ str(self.asList()) +">>"
    

class Grammar:        
      
  def parser_(self, x):
    if x in self._lstParsers:
        return self._lstParsers[x]
    def getParser():
        return self._lstParsers[x]
    return FctParser(getParser)
  
  def text_(self, x):
    return txt(x)
  
  def notInFuture_(self, a):
    return NoFutureCheckerParser(a)
  
  def nothing_(self):    
      return nothing()  

  def anything_(self):
      return item

  def maybe_(self, a):
    return a | nothing()
  
  def many0_(self, a):
    return maxi0(a, ListElem.cloneAndAppend, ListElem())
    return maxi0(marked(a), concat2, ())
  
  def many_(self, a):
    return maxi(a, ListElem.cloneAndAppend, ListElem())
    return maxi(marked(a), concat2, ())
  
  def future_(self, a):
    raise NotImplementedError    
    
  def addParser_(self, name, parser):
    #print "New Parser :", name
    self._lstParsers[name] = parser
    return (name, parser)

  def bind_(self, parser, method):
    if method is not None:
        method = getattr(self._object, method)
        parser = ConvertParser(parser, method)
    return parser

  def conjonction_(self, a, b=None):
    if b is None:
      return a
    return a >> b

  def disjonction_(self, a, op=None, b=None):
    if op is None:
      return a
    return a | b

  def setBinder(self, obj):
    self._object = obj

  def initVals(self, obj):
    self._object = obj
    self._lstParsers = {}

  def __init__(self, obj=None):
    self.initVals(obj)
    def suite(pa, fct):
      def B(a):
        return (((ConstParser(a)["a"] + pa["b"]) >= fct)["a"] / B) | nothing(a)
      return  pa["a"] / B 
  
    def operation_la(pa, op, fct):
      def B(a):
        return (((ConstParser(a)["a"] - op["op"] - pa["b"]) >= fct)["a"] / B) | nothing(a)
      return  pa["a"] / B 

    def postfix(pa, lstOpFct):
      def B(a):
        lstOptions = []
        for op, fct in lstOpFct:
            lstOptions.append(ConstParser(a)["a"] >> op >= fct)
        options = DisjonctionParser(lstOptions)
        return ((optSpaces >> options["a"] >= iden)["a"] / B) | nothing(a)
      return  pa["a"] / B 
      
    #(inList("\"\\/bfnrt"))["a"] >= iden) 
    
    def debug(a):
        print "Debug :", a
        return a
    
    def pureText():
        def isBasic(c):
            if c == '"':
                return Failure
            return c
        basicCharText = item["c"] >= isBasic
        charText = (txt("\\\\", "\\") | txt("\\\"", "\"") | basicCharText )
        return (lit('"') >> manyChars(charText)["a"] >> lit('"') >= iden)

    parserName = word
    methodName = maxiChars(letter|lit("_"))
    
    errorAtom = error(2, "An atom is expected there")
      
    def fct_atom():
      return (
             (lit('(') - expr["a"] - lit(')') >= iden)  |
             (pureText()["x"]        >= self.text_) |
             (parserName["x"]      >= self.parser_) | 
             (lit("!")             >= self.nothing_) |
             (lit("%")             >= self.anything_) |
             errorAtom)
             
            
    atom = FctParser(fct_atom)
    postFixedAtom = postfix(atom, [(lit("?"), self.maybe_),
                                   (lit("*"), self.many0_),
                                   (lit("+"), self.many_),
                                   (lit("!"), self.notInFuture_),
                                   (lit("&"), self.future_),
                                  ]
                               )
    #fact = operation_la(atom, power)
    #exprAnd = suite(postFixedAtom, self.conjonction_)
    bind = ((txt("=>") - methodName["a"] >= iden) | ConstParser(None))
    bindedAtom = postFixedAtom["parser"] - bind["method"] >= self.bind_ 

    exprAnd = operation_la(bindedAtom, optSpaced(lit(",")), self.conjonction_)
    exprOr  = operation_la(exprAnd, optSpaced(lit("|")), self.disjonction_)

    expr = exprOr
    

    assignment = (word["name"] + txt(":") - expr["parser"] - lit(";") >= self.addParser_)

    #self._grammarParser = (optSpaced(expr["a"]) >> eot) >= iden
    
    def get_a(a, b): 
        return a 

    self._grammarParser = optSpaced(suite(assignment, get_a)) |error(5, "parse error")#self._lstParsers["Main"]   

  def getMain(self):
    #print "Liste des parseurs connus : "
    #for k, v in self._lstParsers.iteritems():
    #    print ">", k, v
    main = self._lstParsers["Main"]
    return (filterList(main["a"] >> ~eot) | error(4, "x"))
    
  def parse(self, text):
    parseResult = parse(self._grammarParser, text)
    for n, ares in enumerate(parseResult):
      r, d, dic = ares
      if r:
        return self.getMain()
    else: 
        print "PARSE ERROR"


def filterList(p):
    def list2item(l):
        return l[0]
    return ConvertParser(p, list2item)
    

class Binder:
    def __init__(self):
        self._level = 1

    def isChar(self, items):
        if not items.isalpha():
            return Failure
        return items

    def filter(self, items):
        return NoResult

    def start(self, items):
        self._level = 0
        return NoResult

    def text(self, items):
        if self._level == 0: 
            return "".join(l[0] for l in items[0])
        return NoResult
    
    def open(self, items):
        self._level += 1
        return NoResult
    
    def close(self, items):
        self._level -= 1
        return NoResult

class AnotherGrammar(Grammar):
  def __init__(self):
    self.initVals(self)

  def debug(self, items):
    print "===>", "".join(items[0])
    return items

  def filter(self, items):
    return NoResult

  def isChar(self, items) : 
    if items == "_":
      return items
    if items.isalpha():
      return items
    return Failure

  def isValidTextChar(self, items):
    if items == '"':
        return Failure
    return items

  def isSpaceChar(self, items) :
    if not items.isspace():
        return Failure
    return items

  def isTextSep(self, items):
    if not items == "\"":
        return Failure
    return items
    
  def isEscape(self, items):
    if not items == "\\":
        return Failure
    return items 
 
  def toString(self, items):
    return "".join(items)
   
  def escapedQuote(self, items):
    return '"'

  def escapedEscape(self, items):
    return '\\'

  def postFixMaybe(self, items):
    return self.maybe_

  def postFixMany(self, items):
    return self.many_

  def postFixManyOrZero(self, items):
    return self.many0_

  def postFixInFuture(self, items):
    return self.inFuture_

  def postFixNotInFuture(self, items):
    return self.notInFuture_

  def parserAnything(self, items):
    return self.anything_()

  def parserNothing(self, items):
    return self.nothing_()

  def parserExprParenthesed(self, items):
    return items[1]

  def parserText(self, items):
    return txt("".join(items[1]))

  def parserBindedAtom(self, items):
    parser = items[0]
    method = items[-1]
    if method is not None:
      return self.bind_(parser, method[1])
    return parser

  def parserGetParser(self, items):
    parser = self.parser_(items)
    return parser

  def parserDisjonction(self, items):
    firstParser = items[0]
    if not items[1]:
        return firstParser
    others = list(parser[1] for parser in items[1])
    return DisjonctionParser([firstParser]+others)

  def parserConjonction(self, items):
    firstParser = items[0]
    if not items[1]:
        return firstParser
    others = list(parser[1] for parser in items[1])
    return ConjonctionParser([firstParser]+others)

  def parserPostFixedAtom(self, items):
    atom = items[0]
    for modificator in items[-1]:
         atom = modificator[0](atom)
    return atom

  def parserExpression(self, items):
    return items #| error(7, "Invalid expression")

  def parserAtom(self, items):
    return items #| error(8, "Invalid atom")

  def _parserPostFixedAtom(self, items):
    atom, modificator = items   
    return modificator(atom)

  def newParser(self, items):
    name, _, parser, _ = items
    #print name
    return self.addParser_(name, parser)
  
  def theEnd(self, items):
    pass#self._grammarParser = items
    return items 

def main():           
  text = """
    S           : %       => isSpaceChar;
    Char        : %       => isChar;
    ParserName  : Char+   => toString;
    MethodName  : Char+   => toString;
    Ss          : S*      => filter;
    Anything    : "%"     => parserAnything;
    Nothing     : "!"     => parserNothing;
    TextSep     : %       => isTextSep;
    Escape      : %       => isEscape;
    EscapedEscape : (Escape, Escape) => escapedEscape;
    EscapedSep  :   (Escape, TextSep) => escapedQuote;
    TextChar    : %       => isValidTextChar;
    Maybe       : "?"     => postFixMaybe;
    Many        : "+"     => postFixMany;
    ManyOrZero  : "*"     => postFixManyOrZero;
    InFuture    : "&"     => postFixInFuture;
    NotInFuture : "!"     => postFixNotInFuture;
    OpAnd       : (Ss, ",", Ss);
    OpOr        : (Ss, "|", Ss);
    OpBind      : (Ss, "=>", Ss);
    ExprParenthesed : ("(", Ss, Expr, Ss, ")")                 => parserExprParenthesed;
    Text        : (TextSep, (EscapedEscape | EscapedSep | TextChar)*, TextSep) => parserText;
    PostFix     : Maybe|Many|ManyOrZero|InFuture|NotInFuture ;
    Parser      : ParserName                                   => parserGetParser;
    Atom        : (Parser | Text | Nothing | Anything | ExprParenthesed) => parserAtom;
    PostFixedAtom : (Atom, (Ss, PostFix)*)                     => parserPostFixedAtom;
    BindedAtom  : (PostFixedAtom, (OpBind, MethodName)?)       => parserBindedAtom;
    ExprAnd     : (BindedAtom, (OpAnd, BindedAtom)*)           => parserConjonction;
    ExprOr      : (ExprAnd, (OpOr, ExprAnd)*)                  => parserDisjonction;
    Expr        : ExprOr                                       => parserExpression;
    Line        : (ParserName, Ss, ":", Ss, Expr, Ss, ";")     => newParser;
    Grammar     : (Ss, Line)*, Ss;
    Main        : Grammar                                      => theEnd;
  """

  def run(parser, text):
    result = parse(parser, text)
    for n, ares in enumerate(result):
      r, d, dic = ares
      print "Result found!"
      if r:
        return r
    else:
      print "PARSE ERROR"
    
  grammar1 = Grammar()
  grammar2 = AnotherGrammar()
  grammar3 = AnotherGrammar()
  grammar4 = AnotherGrammar()

  print "Original parser"
  grammar1.setBinder(grammar2)
  parser2 = grammar1.parse(text)

  print "Original parser (simplified)"
  grammar1._grammarParser.simplify()
  parser2 = grammar1.parse(text)

  print "Parsed parser (simplified)"
  grammar2.setBinder(grammar3)
  grammar2._grammarParser = parser2
  grammar2._grammarParser.simplify()
  parser3 = grammar2.parse(text)
  
  print "Parsed parser (simplified)"
  grammar3.setBinder(grammar4)
  grammar3._grammarParser = parser3
  grammar3._grammarParser.simplify()
  parser4 = grammar3.parse(text)


  print "TEST : -------------------------------------------------"
  text2 = """
    Begin  : "(*"                ;         
    End    : "*)"                ;
    Z      : %                    => isChar;
    BeginOpen : Begin => open;
    EndClose: End => close;
    C      : Begin => open , N*, EndClose;
    CC     : C => filter     ;
    N      : CC  | (Begin!, End!, Z);           
    Main   :  ((! => start), N*)                 => text; 
  """   
  grammar4._grammarParser = parser4
  grammar4._grammarParser.simplify()
  
  grammar = grammar4
  grammar.setBinder(Binder())
  p = grammar.parse(text2)
  #print "++++++++"
  #print p
  #print "++++++++"
  #print p.asTree()
  #print "--------"
  #print p.simplify().asTree()
  #print "--------"
  
  print "TEST TEST : --------------------------------------------"
  text3 = "bab(*b(*ba*)b*)b(**)a"*100 
  #print "Input :", text3
  result =parse(p, text3)
  res = result.next()[0].getValue() 
  #print "Output :", res

main()
