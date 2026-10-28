/* Contact is evaluated on building footprints, never on node marker radii. */
(function(root){
  const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  function pointSegment(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],l=dx*dx+dy*dy,t=l?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)}
  function segmentDistance(a,b,c,d){const x=cross(a,b,c),y=cross(a,b,d),z=cross(c,d,a),w=cross(c,d,b);if(((x>0&&y<0)||(x<0&&y>0))&&((z>0&&w<0)||(z<0&&w>0)))return 0;return Math.min(pointSegment(a,c,d),pointSegment(b,c,d),pointSegment(c,a,b),pointSegment(d,a,b))}
  function distance(a,b){if(!a||!b||a.length<3||b.length<3)return Infinity;let best=Infinity;for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++){best=Math.min(best,segmentDistance(a[i],a[(i+1)%a.length],b[j],b[(j+1)%b.length]));if(best===0)return 0}return best}
  function contacts(nodes,tolerance){const result=[];for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j],gap=distance(a.footprint,b.footprint);if(gap<=tolerance)result.push({source:a.id,target:b.id,gap})}return result}
  root.BuildingGeometry={distance,contacts};
})(typeof window==='undefined'?globalThis:window);
