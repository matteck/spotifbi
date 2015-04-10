#/bin/sh
cd ~/src/spotifbi
for show in wendesday-arvo mornings-mon-tue mornings-with-alex-pye mornings-wedtofri thursday-arvo monday-arvo tuesday-arvo utility-fog ears-have-hears sunday-lunch loose-joints; do
	echo $show
	./spot.py $show
done
