import test from 'node:test';
import assert from 'node:assert/strict';
import {fmt,percent,shortId,seriesPath} from '../src/researchgraph/static/ui.mjs';
test('formats finite numbers',()=>assert.equal(fmt(12.345,2),'12.35'));
test('nonfinite numbers are not displayed as measurements',()=>assert.equal(fmt(NaN),'—'));
test('percentage formatter',()=>assert.equal(percent(.825),'82.5%'));
test('identifier truncation',()=>assert.equal(shortId('abcdefghijklmnop'),'abcdefghijkl'));
test('chart path handles missing values',()=>{const path=seriesPath([1,null,3],x=>x,y=>y);assert.equal(path,'M0.00,1.00  M2.00,3.00');});
test('chart path uses line after first sample',()=>assert.equal(seriesPath([1,2],x=>x,y=>y),'M0.00,1.00 L1.00,2.00'));
