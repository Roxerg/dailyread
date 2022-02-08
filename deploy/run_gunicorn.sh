config="gunicorn --workers 1"
while IFS="" read -r p || [ -n "$p" ]
do 
    config+=" --env $p "
done < .env 
config+="wsgi:app"
echo $config
eval "$config"