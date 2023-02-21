### Enhancements

* The CLI now has stronger requirements around the scope used for the Timer
  service, and will treat past Timer tokens as invalid. Users running
  `globus timer` commands will find that they must login agian.
