const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "요청에 실패했습니다.");
  return data;
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

async function loadCourse() {
  try {
    const courses = await api("/api/courses");
    const course = courses[0];
    if (!course) { $("course-info").textContent = "현재 모집 중인 과정이 없습니다."; return; }
    $("course_id").value = course.id;
    $("course-info").textContent =
      `${course.title} · ${course.cohort} · 남은 자리 ${Math.max(course.seats_left, 0)}명`;
    if (course.seats_left <= 0) {
      $("submit").disabled = true;
      $("msg").textContent = "정원이 마감되었습니다.";
      $("msg").className = "err";
    }
    const weeks = await api(`/api/courses/${course.id}/curriculum`);
    const ol = $("weeks");
    ol.replaceChildren(...weeks.map((w) => {
      const li = el("li", w.is_core ? "core" : "");
      const head = el("span", "wk", `${w.week_no}주차`);
      if (w.is_core) head.append(el("span", "tag", "핵심 실습"));
      li.append(head, el("span", "topic", w.topic), el("span", "goal", w.goal || ""));
      return li;
    }));
  } catch (e) {
    $("course-info").textContent = "커리큘럼을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
  }
}

$("form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = $("msg");
  const btn = $("submit");
  const price = $("willing_price").value;
  const payload = {
    course_id: Number($("course_id").value),
    name: $("name").value,
    phone: $("phone").value,
    age_group: $("age_group").value,
    occupation: $("occupation").value,
    willing_price: price === "" ? null : Number(price),
    consent: $("consent").checked,
  };
  btn.disabled = true;
  msg.className = "";
  msg.textContent = "접수 중...";
  try {
    const r = await api("/api/enroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    msg.className = "ok";
    msg.textContent = r.message + " 곧 연락드리겠습니다.";
    $("form").reset();
    loadCourse();
  } catch (e) {
    msg.className = "err";
    msg.textContent = e.message;
  } finally {
    btn.disabled = false;
  }
});

loadCourse();
