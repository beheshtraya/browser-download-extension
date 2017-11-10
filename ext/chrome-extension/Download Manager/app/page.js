function download_check(target)
{
    alert(target);
}


var links = document.getElementsByTagName('a');
for (var i= 0; i < links.length; i++){
    links[i].onclick = download_check(links[i].href);
//    alert(links[i].href);
}