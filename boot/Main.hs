import Control.Monad (when)
import Control.Monad.State
import Data.Char (isAlpha, isAlphaNum)
import Data.Map qualified as Map
import Distribution.Compat.CharParsing (lower)
import Lexer (createLexer, lexAll)
import Parser (createParser, parseAll)

main :: IO ()
main = do
  readdFile <- readFile "./tests/lambda.dal"
  let lexer = createLexer readdFile
      lexerRes = evalState lexAll lexer
      parser = createParser lexerRes
      parsed = evalState parseAll parser
  -- print lexerRes
  print parsed