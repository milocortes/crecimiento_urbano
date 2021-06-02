#!/bin/bash
# Bash Menu Script Example
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

unset options i
while IFS= read -r field1 ; do
  options[i++]="$field1"
done < ./source/zm.txt

echo "%----------------------------------------------------------------------------------------%"
echo "%----------------------------------------------------------------------------------------%"
echo "%----------------------------------------------------------------------------------------%"
printf "${YELLOW}Seleccione alguna Zona Metropolitana para iniciar el preprocesamiento${NC}\n"
echo "%----------------------------------------------------------------------------------------%"
echo "%----------------------------------------------------------------------------------------%"
echo "%----------------------------------------------------------------------------------------%"
echo ""
echo ""
select opt in "${options[@]}" "Salir"; do
  case $opt in
    ZM*)
    echo "--------------------------------------------------------------------------------"
    printf "${YELLOW}Se seleccionó la $opt${NC}\n"
    echo "--------------------------------------------------------------------------------"
      ./source/get_agebs.sh $opt

      # processing
      ;;
    "Salir")
      echo "You chose to stop"
      break
      ;;
    *)
      echo "Escoja una opción válida"
      ;;
  esac
done

## https://askubuntu.com/questions/682095/create-bash-menu-based-on-file-list-map-files-to-numbers
