// scroll-reveal
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target)}}),{threshold:.12});
document.querySelectorAll('.reveal').forEach((el,i)=>{el.style.transitionDelay=(i%4)*80+'ms';io.observe(el)});
// animated counters
document.querySelectorAll('[data-n]').forEach(el=>{const t=+el.dataset.n;new IntersectionObserver((e,o)=>{if(e[0].isIntersecting){o.disconnect();let n=0;const s=Math.max(1,t/50);const id=setInterval(()=>{n=Math.min(t,n+s);el.textContent=Math.round(n);if(n>=t)clearInterval(id)},25)}}).observe(el)});
// 3D tilt on cards and the big cover
document.querySelectorAll('.card,.tilt img').forEach(el=>{el.addEventListener('mousemove',e=>{const r=el.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;el.style.transform=`perspective(800px) rotateY(${x*10}deg) rotateX(${-y*10}deg) translateY(-4px)`});el.addEventListener('mouseleave',()=>el.style.transform='')});
// hero parallax
const st=document.querySelector('.stack');if(st)addEventListener('mousemove',e=>{const x=e.clientX/innerWidth-.5,y=e.clientY/innerHeight-.5;st.querySelectorAll('.float').forEach((f,i)=>f.style.marginLeft=x*(i+1)*18+'px')});
// live bill maths (5% tax)
const d=document.getElementById('disc');if(d){const sub=+document.getElementById('sub').dataset.v,f=n=>'₹'+n.toFixed(2);
const calc=()=>{const p=+d.value,dis=sub*p/100,tx=(sub-dis)*.05;document.getElementById('dv').textContent=p;document.getElementById('dd').textContent='-'+f(dis);document.getElementById('tx').textContent=f(tx);document.getElementById('tt').textContent=f(sub-dis+tx)};d.oninput=calc;calc()}
else{const s=document.getElementById('sub');if(s){const v=+s.dataset.v;document.getElementById('tx').textContent='₹'+(v*.05).toFixed(2);document.getElementById('tt').textContent='₹'+(v*1.05).toFixed(2)}}
