Mano žodynas
============
Evoliucionuojantis Lietuvių kalbos žodynas, skirtas lietuviškų terminų kūrimui
ir suderinimui su Lietuvių kalbos komisija.


Programavimo aplinkos pasiruošimas
==================================
Ubuntu/Debian aplinkoje nusiklonuoti šį projektą. Nueiti į projekto šakninį
katalogą ir įvykdyti komandą ``make`` - jos metu bus paruošiama aplinka darbui.

Su komanda ``make run`` galima paleisti lokalų serverį, kuris naudojamas
programavimo metu. Lokalus serveris pasiekiamas adresu http://127.0.0.1:8000/

Jeigu gaunate klaidą, kurioje paminėtas lxml, tada prieš paleidžiant ``make``
reikia įvykdyti šias komandas:

``sudo apt-get install libxml2-dev libxslt1-dev python-dev``

``sudo apt-get install python-lxml``


Pakeitimų diegimas
==================
Prisijungus su savo github.com paskyra ir nuėjus į projekto repozitorijos
puslapį: https://github.com/niekas/manozodynas reikia šakoti projektą (angl. fork).  
Ties Jūsų paskyra atsiradusiame projekto dublikate atlikti pakeitimus ir
siūlyti apjungti išsišakojusias repozitorijas (angl. pull request). Plačiau:
https://help.github.com/articles/using-pull-requests
