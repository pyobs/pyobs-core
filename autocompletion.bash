function _pyobsd()
{
  latest="${COMP_WORDS[$COMP_CWORD]}"
  prev="${COMP_WORDS[$COMP_CWORD - 1]}"
  words=""
  case "${prev}" in
    start|stop|restart)
      words=`pyobsd list`
      ;;
    *)
      words="start stop restart status";;
  esac
  COMPREPLY=($(compgen -W "$words" -- $latest))
  return 0
}

complete -F _pyobsd pyobsd
