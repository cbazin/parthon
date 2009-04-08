from parthon import *
        
class Grammar:        
      
  def parser_(self, x):
    if x in self._lstParsers:
        return self._lstParsers[x]
    def getParser(): 
        return self._lstParsers[x]
    return FctParser(getParser)
  
  def text_(self, x):
    print "text :", x
    return txt(x)
  
  def notFuture_(self, a):
    return NoFutureCheckerParser(a)
  
  def nothing_(self):    
      return nothing()  

  def maybe_(self, a):
    return a | nothing()
  
  def many0_(self, a):
    return maxi0(marked(a), concat2, ())
  
  def many_(self, a):
    return maxi(marked(a), concat2, ())
  
  def future_(self, a):
    raise NotImplementedError    
    
  def addParser_(self, name, parser):
    self._lstParsers[name] = parser 
    return (name, parser)

  def conjonction_(self, a, b=None):
    if b is None:
      return a
    return a >> b

  def disjonction_(self, a, op=None, b=None):
    if op is None:
      return a
    return a | b

  def __init__(self):
    self._lstParsers = {}
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
        print "###", a
        return a
    
    def pureText():
        charText = (txt("\\\"", "\"") | txt("\\\\", "\\") | notInList("\\\""))
        return (lit('"') >> manyChars(charText)["a"] >> lit('"') >= iden)

    parserName = word
    
    errorAtom = error(2, "An atom is expected there")
      
    def fct_atom():
      return (
             (~lit('(') - expr["a"] - ~lit(')') >= iden)  |
             (pureText()["x"]        >= self.text_) |
             (parserName["x"]      >= self.parser_) | 
             (lit("_")             >= self.nothing_) |
             errorAtom)
             
            
    atom = FctParser(fct_atom)
    postFixedAtom = postfix(atom, [(lit("?"), self.maybe_),
                                   (lit("*"), self.many0_),
                                   (lit("+"), self.many_),
                                   (lit("!"), self.notFuture_),
                                   (lit("&"), self.future_),
                                  ]
                               )
    #fact = operation_la(atom, power)
    #exprAnd = suite(postFixedAtom, self.conjonction_)
    exprAnd = operation_la(postFixedAtom, optSpaced(lit(",")), self.conjonction_)
    exprOr  = operation_la(exprAnd, optSpaced(lit("|")), self.disjonction_)

    expr = exprOr
    
    assignment = word["name"] - txt("<-") - expr["parser"] - lit(";") >= self.addParser_

    #self._grammarParser = (optSpaced(expr["a"]) >> eot) >= iden
    
    def get_a(a, b): 
        return a 

    self._grammarParser = optSpaced(suite(assignment, get_a))#self._lstParsers["Main"]   

  def getMain(self):
    for k, v in self._lstParsers.iteritems():
        print k, v
    return self._lstParsers["Main"]["a"] >> eot >= iden
    
  def parse(self, text):
    print text
    try:
      parseResult = parse(self._grammarParser, text)
    except ParseError, e:
      print e
    for n, ares in enumerate(parseResult):
      r, d, dic = ares
      print "/////////////////////////////////////////"
      if r:
        print r
        #print "res (%2d): %s, %s, %s" % (n, r, repr(''.join(d)), dic)
        #print "++++++++"
        #print r.getValue()
        #print "++++++++"
        #print r.getValue().asTree()
        #print "--------"
        #print r.getValue().simplify().asTree()
        #print "--------"
        break          
    else: 
        print "PARSE ERROR"
   
        
def main():            
  #text = '"a?\\"bba"|(b?|c     c)|"aa"|"bb"'
  text = """
    Begin <- "(*";
    End <- "*)";
    Z <- "a"|"bb"|"b";
    N <- C|(Begin!, End!, Z);
    C <- Begin, N*, End; 
    Main <- N*; 
  """   
  #text = """
  #  Main <- "a";
  #""" 
  g = Grammar()
  print g._grammarParser.asTree()
#  print repr(g._grammarParser)
#  print g._grammarParser.asText()
  #try:
  g.parse(text)
  p = g.getMain()
  print "++++++++"
  print p
  print "++++++++"
  print p.asTree()
  print "--------"
  print p.simplify().asTree()
  print "--------"
 
  text = "a(*abababb(*b*)bbb*)" 
  parseResult = parse(p, text)
  
  for n, ares in enumerate(parseResult):
    r, d, dic = ares
    print "/////////////////////////////////////////"
    if r:
      print r
      break
    else:
        print "PARSE ERROR"
  else: 
    print "ERROR parsing <%s>"% text
  
main()
