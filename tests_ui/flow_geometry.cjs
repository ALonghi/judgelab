// Verify the diagram's orthogonal connectors against the rendered node outlines.
const assert = require('node:assert/strict');

function pathEnds(path) {
  const commands = [...path.matchAll(/([MLHV])\s*(-?\d+(?:\.\d+)?)(?:[ ,]+(-?\d+(?:\.\d+)?))?/g)];
  assert.equal(commands.map(match => match[0]).join('').replace(/[ ,]/g, ''), path.replace(/[ ,]/g, ''));
  assert.equal(commands[0]?.[1], 'M');
  let point, start;
  for (const [, command, first, second] of commands) {
    if (command === 'M' || command === 'L') {
      assert.notEqual(second, undefined);
      point = [Number(first), Number(second)];
    } else if (command === 'H') point = [Number(first), point[1]];
    else point = [point[0], Number(first)];
    start ||= point;
  }
  return [start, point];
}

function arc(cx, cy, rx, ry, from, to) {
  return Array.from({length: 33}, (_, i) => {
    const angle = from + (to - from) * i / 32;
    return [cx + rx * Math.cos(angle), cy + ry * Math.sin(angle)];
  });
}

function outline({x, y, w, h, shape}) {
  if (shape === 'decision') return [[x+w/2,y],[x+w,y+h/2],[x+w/2,y+h],[x,y+h/2]];
  if (shape === 'database') return [
    ...arc(x+w/2,y+14,w/2,14,Math.PI,2*Math.PI),
    ...arc(x+w/2,y+h-14,w/2,14,0,Math.PI),
  ];
  if (shape === 'document') {
    const points = [[x,y],[x+w,y],[x+w,y+h-10]];
    for (const [start, control, end] of [
      [[x+w,y+h-10],[x+w*.75,y+h-22],[x+w/2,y+h-10]],
      [[x+w/2,y+h-10],[x+w*.25,y+h+2],[x,y+h-10]],
    ]) for (let i=1; i<=32; i++) {
      const t=i/32;
      points.push(start.map((value,j)=>(1-t)**2*value+2*(1-t)*t*control[j]+t*t*end[j]));
    }
    return points;
  }
  const radius = shape === 'terminal' ? Math.min(h/2,w/2) : 2;
  return [
    ...arc(x+w-radius,y+radius,radius,radius,-Math.PI/2,0),
    ...arc(x+w-radius,y+h-radius,radius,radius,0,Math.PI/2),
    ...arc(x+radius,y+h-radius,radius,radius,Math.PI/2,Math.PI),
    ...arc(x+radius,y+radius,radius,radius,Math.PI,Math.PI*1.5),
  ];
}

function segmentDistance(point, start, end) {
  const dx=end[0]-start[0], dy=end[1]-start[1];
  const length=dx*dx+dy*dy;
  const t=length ? Math.max(0,Math.min(1,((point[0]-start[0])*dx+(point[1]-start[1])*dy)/length)) : 0;
  return Math.hypot(point[0]-start[0]-t*dx,point[1]-start[1]-t*dy);
}

function disconnectedEnds(graph) {
  const outlines=graph.nodes.map(outline);
  return graph.edges.flatMap((edge,index)=>pathEnds(edge.path).flatMap((point,end)=>{
    // Two viewBox units allow for the node stroke and rounded integer anchors.
    const touches=outlines.some(points=>points.some((a,i)=>segmentDistance(point,a,points[(i+1)%points.length])<=2));
    return touches ? [] : [`edge ${index} ${end ? 'end' : 'start'} at ${point.join(',')}`];
  }));
}

module.exports = {disconnectedEnds};
