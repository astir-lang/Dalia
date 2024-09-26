import Control.Monad (when)
import Control.Monad.State
import Data.Char (isAlpha, isAlphaNum)
import Data.Map qualified as Map
import Lexer (createLexer, lexAll)
import LowerStep1 (createStairCase)

main :: IO ()
main = do
  readdFile <- readFile "./tests/1.cyl"
  let lexer = createLexer readdFile
      lexerRes = evalState lexAll lexer
      lower = createStairCase lexerRes
  print lexerRes
