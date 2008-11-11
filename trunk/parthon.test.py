from parthon import *

def simplify(parser):
    parserType = parser.__class__
    if parserType in (ConjonctionParser, DisjonctionParser):
        newChildren = []
        for child in parser.getChildren():
            simplify(child)
            childType = child.__class__
            if childType != parserType:
                newChildren.append(child)
                continue
            for grandChild in child.getChildren():
                newChildren.append(grandChild)
        parser.setChildren(newChildren) 
    return parser

        
class Grammar:        
      
  def parser_(self, x):
    return NamedParser(x)
  
  def text_(self, x):
    print x
    return txt(x)
  
  def not_(self, a):
    return x >> fail()
  
  def nothing_(self):    
      return nothing()  

  def maybe_(self, a):
    return a | nothing()
  
  def many0_(self, a):
    return maxi0(marked(x), concat2, ())
  
  def many_(self, a):
    return maxi(marked(x), concat2, ())
  
  def future_(self, a):
    raise NotImplementedError    
    
  def conjonction_(self, a, op=None, b=None):
    if op is None:
      return a
    return a >> b

  def disjonction_(self, a, op=None, b=None):
    if op is None:
      return a
    return a | b
        

  def __init__(self):    
    def operation_la(pa, op, fct):
      def B(a):
        return (((ConstParser(a)["a"] - op["op"] - pa["b"]) >= fct)["a"] / B) | (nothing() >= (lambda: a))
      return  pa["a"] / B 

    def operator_ra(pa, lstOpFct):
      def B(a):
        lstOptions = []
        for op, fct in lstOpFct:
            lstOptions.append(ConstParser(a)["a"] >> op >= fct)
        options = DisjonctionParser(lstOptions)
        return (((optSpaces >> options["a"] >= iden)["a"]) / B) | (nothing() >= (lambda: a))
      return  pa["a"] / B 
      
    charText = txt("\\\"", "\"") | txt("\\\\", "\\") | notInList("\\\"")
               
               
               #(inList("\"\\/bfnrt"))["a"] >= iden) 
     
    pureText = (lit('"') >> manyChars(charText)["a"] >> lit('"') >= iden)
    parserName = word
      
    def fct_atom():
      return (
             (lit('(') - expr["a"] - lit(')') >= iden)  |
             (pureText["x"]        >= self.text_) |
             (parserName["x"]      >= self.parser_) | 
             (lit("_")             >= self.nothing_)
             )
             
             
    atom = FctParser(fct_atom)
    postFixedAtom = operator_ra(atom, [(lit("?"), self.maybe_),
                                       (lit("*"), self.many0_),
                                       (lit("+"), self.many_),
                                       (lit("!"), self.not_),
                                       (lit("&"), self.future_),
                                      ]
                               )
    #fact = operation_la(atom, power)
    exprAnd = operation_la(postFixedAtom, lit(","), self.conjonction_)
    exprOr  = operation_la(exprAnd, lit("|"), self.disjonction_)

    expr = exprOr
    
    self._grammarParser = (optSpaces >> expr["a"] >> optSpaces >> eot) >= iden

    
  def parse(self, text):
    for n, ares in enumerate(parse(self._grammarParser, text)):
      r, d, dic = ares
      print "/////////////////////////////////////////"
      print text
      if r:
        #print "res (%2d): %s, %s, %s" % (n, r, repr(''.join(d)), dic)
        print "++++++++"
        print r.getValue()
        print simplify(r.getValue()).asText()
        print "--------"
        break          

def main():            
  text = '"a?\\"bba"|(b?|c,c)'
      
  g = Grammar()
  print g._grammarParser.asTree()
  print repr(g._grammarParser)
  print g._grammarParser.asText()
  #try:
  p = g.parse(text)
  #except:
  #  print "ERROR parsing <%s>"% text
  
main()