const fs = require("fs");
const { browserSync } = require("vibium");

/* =========================
   유틸: sleep (동기)
========================= */
function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

/* =========================
   유틸: selector 나올 때까지 기다리기
========================= */
function waitForSelector(vibe, selector, {
  timeoutMs = 10000,
  intervalMs = 300
} = {}) {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    try {
      return vibe.find(selector);
    } catch {
      sleep(intervalMs);
    }
  }

  throw new Error(`❌ Timeout waiting for selector: ${selector}`);
}

/* =========================
   테스트 시작
========================= */
const vibe = browserSync.launch({
  headless: false   // 👀 눈으로 보기
});

try {
  console.log("① 메인 페이지 접속");
  vibe.go("https://the-internet.herokuapp.com/");
  sleep(1000);

  fs.writeFileSync("step-01-main.png", vibe.screenshot());

  console.log("② Form Authentication 링크 대기");
  const loginLink = waitForSelector(vibe, 'a[href="/login"]');
  sleep(500);
  loginLink.click();

  console.log("③ 로그인 페이지 로딩 대기");
  waitForSelector(vibe, "#username");
  fs.writeFileSync("step-02-login-page.png", vibe.screenshot());

  console.log("④ 계정 정보 입력");
  vibe.find("#username").value = "tomsmith";
  vibe.find("#password").value = "SuperSecretPassword!";
  sleep(500);

  console.log("⑤ 로그인 버튼 클릭");
  vibe.find('button[type="submit"]').click();

  console.log("⑥ 결과 메시지 대기");
  const message = waitForSelector(vibe, "#flash");
  fs.writeFileSync("step-03-result.png", vibe.screenshot());

  console.log("결과 메시지:", message.textContent.trim());

  console.log("✅ 테스트 성공! 5초 후 종료합니다...");
  sleep(5000);

} catch (err) {
  console.error("❌ 테스트 실패:", err.message);
  fs.writeFileSync("error.png", vibe.screenshot());
  console.log("error.png 저장됨");
} finally {
  vibe.quit();
}