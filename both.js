localStorageAvailable = true;
try{localStorage.setItem('test','0');
localStorage.removeItem('test');
}catch(e){
localStorageAvailable = false;}

d = document; b = d.body; r = d.querySelector(':root');
b1 = d.querySelector('#a'); b2 = d.querySelector('#b');
b3 = d.querySelector('#c'); b4 = d.querySelector('#d');
b5 = d.querySelector('#e');
sidebar = d.querySelector('.sidebar');
title = d.querySelectorAll('.title');
channel = d.querySelectorAll('.channel');
info = d.querySelectorAll('.info');
buttons = Array.from(d.querySelector('.buttons').children);
statsP = d.querySelector('.stats').querySelectorAll('p');
delay = '230ms'; bezier = 'ease-in';

function theme(button, ...colors){
button.addEventListener('click', function(){
    b.style.cssText=`background:${colors[0]};transition-duration:${delay};
        transition-timing-function:${bezier}`
    sidebar.style.cssText=`background:${colors[1]};transition-duration:${delay};
        transition-timing-function:${bezier}`
    r.style.setProperty('--start', colors[2])
    title.forEach(i => i.style.cssText=`color:${colors[3]};
        transition-duration:${delay};transition-timing-function:${bezier}`)
    channel.forEach(i => i.style.cssText=`color:${colors[4]};
        transition-duration:${delay};transition-timing-function:${bezier}`)
    info.forEach(i => i.style.cssText=`color:${colors[5]};
        transition-duration:${delay};transition-timing-function:${bezier}`)
    buttons.forEach(i => i.style.cssText=`background:${colors[6]};
        transition-duration:${delay};transition-timing-function:${bezier}`)
    statsP.forEach(i => i.style.cssText=`color:${colors[7]};
        transition-duration:${delay};transition-timing-function:${bezier}`)
    if(localStorageAvailable == true){
    localStorage.setItem('body', colors[0]);
    localStorage.setItem('sidebar', colors[1]);
    localStorage.setItem('start', colors[2]);
    localStorage.setItem('title', colors[3]);
    localStorage.setItem('channel', colors[4]);
    localStorage.setItem('info', colors[5]);
    localStorage.setItem('buttons', colors[6]);
    localStorage.setItem('statsP', colors[7]);}})}
theme(b1,'#212126','#0F0E0F','#41414D','#F0F0F0','#BCB8F2','#B5B5B5','#59545C','#C7C7C7')
theme(b2,'#121212','#262626','#2B2B2E','#CCCCCC','#A8B2DB','#8D91A6','#736C6C','#D4CECE')
theme(b3,'#23272B','#101516','#383E45','#FFF','#E6E6E6','#C2C2C2','#5E5C61','#C1BDC9')
theme(b4,'#222224','#404142','#4F4A4C','#F7F7F7','#C3C8ED','#BFBFBF','#8F8888','#F0F0F0')
theme(b5,'#3D3B3C','#5C5C5C','#615960','#FFF','#ECDEFF','#CED0D9','#8F8F8F','#D9C3C3')/*42414D*/

if(localStorageAvailable == true){
if(localStorage.getItem('body') != null){
    b.style.cssText=`background:${localStorage.getItem('body')};`
    sidebar.style.cssText=`background:${localStorage.getItem('sidebar')};`
    r.style.setProperty('--start', localStorage.getItem('start'))
    title.forEach(i => i.style.cssText=`color:
        ${localStorage.getItem('title')};`)
    channel.forEach(i => i.style.cssText=`color:
        ${localStorage.getItem('channel')};`)
    info.forEach(i => i.style.cssText=`color:${localStorage.getItem('info')};`)
    buttons.forEach(i => i.style.cssText=`color:
        ${localStorage.getItem('buttons')};`)
    statsP.forEach(i => i.style.cssText=`color:
        ${localStorage.getItem('statsP')};`)}}

mainTitle = d.querySelector('title').text
if(mainTitle=='Recommended'){
    stats = d.querySelector('.stats')
    channels = stats.querySelector('p').textContent.slice(0,stats.querySelector('p').textContent.search(' '))
    videos = stats.querySelectorAll('p')[1].textContent.slice(0,stats.querySelectorAll('p')[1].textContent.search(' '))
    ratioWidth = parseInt(channels*100/videos)
    ratio = stats.querySelector('.ratio2')
    ratio.style.width = ratioWidth+'px'
}

length = d.querySelectorAll('.length')
wd = 0
length.forEach(i => {
lengthType = i.querySelector('p')
lengthTime = i.querySelectorAll('p')[1]
lty = getComputedStyle(lengthType).getPropertyValue('width')
if(lengthType.textContent == ''){
    if(lengthTime.textContent.length == 5){
    wd = 42; i.style.cssText = `width:${wd}px;margin-left:-45px;`}
    else if(lengthTime.textContent.length == 4){
    wd = 36; i.style.cssText = `width:${wd}px;margin-left:-39px;`}
    else if(lengthTime.textContent.length == 7){
    wd = 56; i.style.cssText = `width:${wd}px;margin-left:-59px;`}
    else if(lengthTime.textContent.length == 8){
    wd = 64; i.style.cssText = `width:${wd}px;margin-left:-67px;`}}
else if(lengthType.textContent == 'streaming..'){
    wd = 82
    i.style.cssText = `width:${wd}px;margin-left:-85px;`
    lengthType.style.cssText = `margin-top:2px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`;}
else if(lengthType.textContent == 'streamed'){
    wd = 64
    i.style.cssText = `width:${wd}px;margin-left:-67px;height:32px;margin-top:101px;`
    lengthType.style.cssText = `margin-top:16px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`}
else if(lengthType.textContent == 'premiered'){
    wd = 68;
    i.style.cssText = `width:${wd}px;margin-left:-71px;height:35px;margin-top:98px;`
    lengthType.style.cssText = `margin-top:17px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`}
else if(lengthType.textContent == 'premiering..'){
    wd = 90
    i.style.cssText = `width:${wd}px;margin-left:-93px;height:35px;margin-top:98px;`
    lengthType.style.cssText = `margin-top:17px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`}
else if(lengthType.textContent == 'short'){
    wd = 42
    i.style.cssText = `width:${wd}px;margin-left:-45px;height:35px;margin-top:98px;`
    lengthType.style.cssText = `margin-top:17px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`}
else if(lengthType.textContent == 'premiere'){
    wd = 63;
    i.style.cssText = `width:${wd}px;margin-left:-66px;height:35px;margin-top:98px;`
    lengthType.style.cssText = `margin-top:17px;margin-left:${(parseInt(wd)-parseInt(lty))/2}px;`}



lti = getComputedStyle(lengthTime).getPropertyValue('width')
lengthTime.style.cssText = `margin-left:${(parseInt(wd)-parseInt(lti))/2}px;`


})
