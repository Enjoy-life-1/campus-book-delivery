<template>
  <div v-if="visible" class="sms-wh-overlay" @click.self="close">
    <div class="sms-wh-box" role="dialog" aria-labelledby="smsWhTitle">
      <div class="sms-wh-head">
        <h5 id="smsWhTitle"><i class="fa fa-commenting-o me-2"></i>短信验证码（Webhook 模式）</h5>
        <button type="button" class="sms-wh-close" aria-label="关闭" @click="close"><i class="fa fa-times"></i></button>
      </div>
      <div class="sms-wh-body">
        <p class="sms-wh-warn">当前为 Webhook 测试模式，<strong>验证码不会发到手机</strong>。</p>
        <ol>
          <li>先运行项目根目录的「<strong>启动短信Webhook.bat</strong>」</li>
          <li>在 Webhook 黑窗口或 <code>logs/sms_webhook.log</code> 中查看 6 位验证码</li>
          <li>将验证码填入上方输入框完成注册/重置</li>
        </ol>
        <p v-if="detail" class="sms-wh-detail">{{ detail }}</p>
      </div>
      <div class="sms-wh-foot">
        <button type="button" class="btn btn-success w-100" @click="close">知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Webhook 短信模式说明弹窗
import { useSmsWebhookHint } from '@/composables/useSmsWebhookHint'
const { visible, detail, close } = useSmsWebhookHint()
</script>

<style scoped>
.sms-wh-overlay {
  position: fixed;
  inset: 0;
  z-index: 10050;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.sms-wh-box {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}
.sms-wh-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid #eee;
}
.sms-wh-head h5 {
  margin: 0;
  font-size: 1.05rem;
  color: #2c5530;
}
.sms-wh-close {
  border: none;
  background: none;
  font-size: 1.1rem;
  color: #888;
  cursor: pointer;
  padding: 4px 8px;
}
.sms-wh-body {
  padding: 18px 20px;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #333;
}
.sms-wh-warn {
  background: #fff8e6;
  border: 1px solid #ffe08a;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 14px;
  color: #856404;
}
.sms-wh-body ol {
  margin: 0;
  padding-left: 1.25rem;
}
.sms-wh-body li + li {
  margin-top: 6px;
}
.sms-wh-body code {
  background: #f4f4f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.88em;
}
.sms-wh-detail {
  margin: 14px 0 0;
  font-size: 0.85rem;
  color: #666;
}
.sms-wh-foot {
  padding: 0 20px 18px;
}
</style>
