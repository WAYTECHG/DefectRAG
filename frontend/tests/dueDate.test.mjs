import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULT_DUE_TIME,describeDue,dueParts,joinDue,relativeDay,shortcutDate,timeLabel,timeOptions} from '../src/dueDate.mjs';

const now=new Date(2026,9,31,10,30);

test('shortcuts count calendar days from today, across month ends',()=>{
 assert.equal(shortcutDate(1,now),'2026-11-01');
 assert.equal(shortcutDate(3,now),'2026-11-03');
 assert.equal(shortcutDate(7,now),'2026-11-07');
 assert.equal(shortcutDate(14,now),'2026-11-14');
});

test('a picked date keeps the chosen time and starts at 5:00 PM',()=>{
 assert.equal(joinDue('2026-11-03',''),'2026-11-03T'+DEFAULT_DUE_TIME);
 assert.equal(joinDue('2026-11-03','09:30'),'2026-11-03T09:30');
 assert.equal(joinDue('',DEFAULT_DUE_TIME),'');
 assert.deepEqual(dueParts('2026-11-03T09:30'),{date:'2026-11-03',time:'09:30'});
});

test('time list covers working hours and keeps an existing off-grid time',()=>{
 const list=timeOptions();
 assert.equal(list[0],'07:00');assert.equal(list.at(-1),'20:00');assert.equal(list.length,27);
 assert.ok(timeOptions('11:04').includes('11:04'));
 assert.equal(timeLabel('17:00'),'5:00 PM');assert.equal(timeLabel('00:30'),'12:30 AM');assert.equal(timeLabel('12:00'),'12:00 PM');
});

test('the summary reads like a sentence with a relative day',()=>{
 assert.equal(relativeDay('2026-10-31T17:00',now),'today');
 assert.equal(relativeDay('2026-11-01T17:00',now),'tomorrow');
 assert.equal(relativeDay('2026-11-07T17:00',now),'in 7 days');
 assert.equal(relativeDay('2026-10-29T17:00',now),'2 days ago');
 assert.equal(describeDue('2026-11-03T17:00',now),'Tuesday, 3 Nov 2026 at 5:00 PM · in 3 days');
 assert.equal(describeDue('',now),'');assert.equal(describeDue('not-a-date',now),'');
});
