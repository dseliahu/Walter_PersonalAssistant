LEADING_PLEASANTRIES = ["could you", "can you", "would you", "will you", "please", "thank you"]
TRAILING_PLEASANTRIES = ["please"]


def stripPleasantries(message):
  for pleasantry in LEADING_PLEASANTRIES:
    pleasantry = pleasantry + " "
    if message.startswith(pleasantry):
      message = message[len(pleasantry):]

  for pleasantry in TRAILING_PLEASANTRIES:
    pleasantry = " " + pleasantry
    if message.endswith(pleasantry):
      message = message[:-len(pleasantry)]

  return message



class Phrase(object):

  def __init__(self, sourceString):
    self.blocks = []
    self.vars = []

    sourceString = sourceString.strip()
    while True:
      index = sourceString.find('<')
      if index == -1:
        if len(sourceString) > 0:
          self.blocks.append(sourceString.strip())
        break
      elif index == 0:
        raise ValueError("Source string cannot start with a variable or have back to back variables.")


      self.blocks.append(sourceString[:index-1].strip())
      sourceString = sourceString[index+1:]

      index = sourceString.find('>')
      if index == -1:
        raise ValueError("Unbalanced <> in source string for phrase.")

      self.vars.append(sourceString[:index].strip())
      sourceString = sourceString[index+1:].strip()

    # print(self.blocks)
    # print(self.vars)



  def checkMessage(self, message):
    message = stripPleasantries(message)
    args = {}
    blockIndex = 0
    varIndex = 0
    match = True

    while blockIndex < len(self.blocks):
      if message.startswith(self.blocks[blockIndex]):
        message = message[len(self.blocks[blockIndex]):]
        if varIndex < len(self.vars):
          if blockIndex == len(self.blocks) - 1:
            args[self.vars[varIndex]] = message.strip()
          else:
            index = message.find(self.blocks[blockIndex+1])
            if index == -1:
              # print("here")
              match = False
              break
            else:
              args[self.vars[varIndex]] = message[:index].strip()
              message = message[index:].strip()
      else:
        match = False
        break
      blockIndex = blockIndex + 1
      varIndex = varIndex + 1

    return (match, args)






class messageManager(object):

  def __init__(self):
    self.rules = [] #array of tuples (phrase, callback)
    self.defaultCallback = None


  def newRule(self, sourceString, callback):
    phrase = Phrase(sourceString)
    self.rules.append((phrase, callback))

  def setDefaultCallback(self, callback):
    self.defaultCallback = callback

  def processMessage(self, message):
    for rule in self.rules:
      phrase = rule[0]
      callback = rule[1]
      match = phrase.checkMessage(message)
      isMatch = match[0]
      args = match[1]
      if isMatch:
        callback(args)
        return

    if self.defaultCallback is not None:
      self.defaultCallback(stripPleasantries(message))








