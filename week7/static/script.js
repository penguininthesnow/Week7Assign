async function api(path, options = {}) {
    const res = await fetch(path, {
        credentials: "include",
        ...options
    });
    return res.json();
}

// 註冊頁面
const signupBtn=document.getElementById("btnSignup");
if(signupBtn) {
    signupBtn.addEventListener("click", async() => {
        const name = document.getElementById("signupName").value.trim();
        const email = document.getElementById("signupEmail").value.trim();
        const password = document.getElementById("signupPassword").value.trim();
        const agree = document.getElementById("agreebox");
        const output = document.getElementById("signupResult");

        if(agree && !agree.checked) {
            alert("請勾選同意條款");
            return;
        }
        if(!name || !email || !password) {
            output.textContent = "請輸入完整資料";
            return;
        }

        const res = await api("/api/signup", {
            method: "POST",
            body: new URLSearchParams({ name, email, password })    
        });

        if(res.ok) {
            output.textContent = "註冊成功，請重新登入!"
        } else {
            output.textContent = res.message || "註冊失敗，Email已存在";
        }
    });
}

// 登入頁面 index.html
const loginBtn=document.getElementById("btnLogin");
if(loginBtn) {
    loginBtn.addEventListener("click", async () =>{
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value.trim();
        const output = document.getElementById("loginResult");
        
        if(!email || !password) {
            alert("請輸入帳號密碼");
            return;
        }

        const res = await api("/api/login", {
            method: "POST",
            body: new URLSearchParams({ email, password })    
        });

        if(res.ok) {
            alert("登入成功!");
            window.location.href = "/static/member.html";
        } else {
            output.textContent = "帳號密碼錯誤";
        }
    });
}

// 會員頁面
async function loadMemberInfo() {
    const welcome=document.getElementById("welcomeText");
    if(!welcome) return;
    
    const res = await api("/api/me");
    const user = res.data;

    if(!user) {
        alert("尚未登入，請重新登入");
        window.location.href = "/static/index.html";
        return;
    }

    welcome.textContent = `${user.name}，歡迎登入系統`;

    // 載入查詢過我
    loadQueryLog(user.id);
}
loadMemberInfo();

// 登出頁面
const logoutBtn = document.getElementById("btnLogout");
if(logoutBtn) {
    logoutBtn.addEventListener("click", async()=>{
        await api("/api/logout", {  method:"POST" });
        alert("已登出");
        window.location.href = "/static/index.html";
    });
}

// task2: 查詢會員資料
const btnQuery = document.getElementById("btnQuery");
if(btnQuery) {
    btnQuery.addEventListener("click", async ()=>{
        const id = document.getElementById("queryMemberId").value.trim();
        const output = document.getElementById("queryResult");

        if(!id) {
            output.textContent="輸入會員id";
            return;
        }
        const res = await api(`/api/member/${id}`)

        if(!res.data) {
            output.textContent = "查無會員資料";
        } else {
            output.innerHTML= `
            <div><strong></strong> ${res.data.name}(</strong> ${res.data.email})</div>
            <div><strong></div>
            `;
        }

        // 查詢結束後，自動更新自己的查詢紀錄
        const me = await api("/api/me");
        if (me.data) loadQueryLog(me.data.id);
        
    });
}

// task3: 更新姓名
const btnUpdateName = document.getElementById("btnUpdateName");
if (btnUpdateName) {
    btnUpdateName.addEventListener("click", async() => {
        const newName = document.getElementById("newName").value.trim();
        const output = document.getElementById("updateResult");
        
        if (!newName) {
            output.textContent="新的名稱";
            return;
        }

        const res = await api("/api/member",{
            method: "PATCH",
            headers: { "Content-Type": "application/json"},
            body: JSON.stringify({ name: newName })
        });

        if (res.ok) {
            output.textContent = "更新成功!";
            loadMemberInfo();
        } else {
            output.textContent = "更新失敗~";
        }
    });
}

// task 4: 查詢紀錄
async function loadQueryLog(member_id) {
    const list = document.getElementById("logList");
    if (!list) return;
    
    const res = await api(`/api/member/${member_id}/query-log`);

    if(!res.data) {
        list.innerHTML = "<li>沒有查詢紀錄</li>";
        return;
    }

    if(!res.data || res.data.length === 0) {
        list.innerHTML = "<li>無查詢紀錄</li>";
        return;
    }

    list.innerHTML = "";
    res.data.forEach(log => {
        const li = document.createElement("li");
        li.textContent = `${log.searcher_name} ( ${log.searched_at})`;
        list.appendChild(li);
    });
}