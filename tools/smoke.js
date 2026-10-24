// 由 tools/check.py 呼叫：用假的瀏覽器環境把網頁程式完整跑一次，抓執行時才會出現的錯誤
const fs=require("fs");
const src=fs.readFileSync(process.argv[2],"utf8");
const make=()=>{const f=function(){};return new Proxy(f,{
  get(t,k){if(k===Symbol.toPrimitive)return h=>h==="number"?0:"";if(k==="then")return undefined;
    if(k===Symbol.iterator)return function*(){};if(typeof k==="symbol")return undefined;
    if(!(k in store(t))&&["value","textContent","innerHTML","innerText"].includes(k))return "";if(!(k in store(t)))store(t)[k]=make();return store(t)[k]},
  set(t,k,v){store(t)[k]=v;return true},apply(){return make()},construct(){return make()}})};
const S=new WeakMap();function store(t){if(!S.has(t))S.set(t,{});return S.get(t)}
const ls={};global.localStorage={getItem:k=>k in ls?ls[k]:null,setItem:(k,v)=>ls[k]=String(v),removeItem:k=>delete ls[k]};
global.document=make();global.window=global;global.innerWidth=1024;global.scrollY=0;
global.location={hash:"",pathname:"/",search:""};global.history={replaceState(){}};
global.matchMedia=()=>({matches:false});global.navigator={};global.addEventListener=()=>{};global.scrollTo=()=>{};
global.QRCode=make();global.Image=function(){};global.CSS={escape:s=>s};
new Function(src+"\n;globalThis.__api={DISHES,makePlan,M,planDays,mealKcal,renderPlan,renderText,render,encodePlan,decodePlan,shopData,costOf};")();
const a=globalThis.__api;
for(const meal of ["1+1","2","2+1","3","3+1","pot"]){a.M.meal=meal;a.M.days=[0,1,2,3,4,5,6];a.makePlan();
  for(const d of a.planDays())if(!Number.isFinite(a.mealKcal(a.M.plan[d].map(r=>r.n))))throw new Error("熱量算不出來："+meal);}
a.render("");a.renderText();a.shopData();
if(!a.decodePlan(a.encodePlan()))throw new Error("分享連結無法還原");
console.log("OK");
