    -- Roblox Studio AI Helper Plugin
    -- 이 스크립트는 로블록스 스튜디오의 Local Plugin 위치에 저장되어야 합니다.
    -- (C:\Users\<유저명>\AppData\Local\Roblox\Plugins 등)

    local HttpService = game:GetService("HttpService")
    local Selection = game:GetService("Selection")

    local LOCAL_API_URL = "http://127.0.0.1:8000/poll"
    local POLLING_INTERVAL = 1.0

    local isPolling = true

    -- HttpService 활성화 체크
    if not pcall(function() HttpService:GetAsync("http://google.com") end) then
        warn("⚠️ AI Helper를 사용하려면 Game Settings -> Security -> 'Allow HTTP Requests'를 켜야 할 수 있습니다.")
        warn("다만 로컬 호스트 요청은 설정 없이 가능할 수도 있으니 계속 진행합니다.")
    end

    -- 특정 이름을 가진 객체를 시각적으로 강조하는 함수
    local function highlightPart(partName)
        local part = workspace:FindFirstChild(partName, true)
        if part and part:IsA("BasePart") then
            local hl = part:FindFirstChild("AI_Highlight")
            if not hl then
                -- 확실한 시각적 테두리 효과를 위해 Highlight 인스턴스 사용
                hl = Instance.new("Highlight")
                hl.Name = "AI_Highlight"
                hl.FillColor = Color3.fromRGB(255, 255, 0) -- 노란색 틴트
                hl.FillTransparency = 0.5
                hl.OutlineColor = Color3.fromRGB(255, 0, 0) -- 빨간 고선명 테두리
                hl.OutlineTransparency = 0
                hl.Parent = part
            end
            print("🤖 AI Helper: " .. partName .. " 객체를 강조했습니다.")
            Selection:Set({part})
        else
            warn("🤖 AI Helper: " .. tostring(partName) .. " 이름을 가진 파트를 찾을 수 없습니다.")
        end
    end

    -- 명령 처리 핸들러
    local function processCommand(commandType, commandData)
        if commandType == "HIGHLIGHT_PART" then
            highlightPart(commandData.part_name)
        elseif commandType == "INSERT_CODE" then
            warn("코드 자동 삽입 기능은 권한 문제 확인 및 ScriptEditorService 연동이 필요합니다.")
        else
            print("🤖 AI Helper: 알 수 없는 명령 수신됨:", commandType)
        end
    end

    -- 주기적으로 로컬 API 서버(Python)에 명령 호출 반복 (Polling)
    task.spawn(function()
        while isPolling do
            local success, response = pcall(function()
                return HttpService:RequestAsync({
                    Url = LOCAL_API_URL,
                    Method = "GET"
                })
            end)

            if success and response.Success then
                local data = HttpService:JSONDecode(response.Body)
                if data.has_command then
                    processCommand(data.command_type, data.command_data)
                end
            end

            task.wait(POLLING_INTERVAL)
        end
    end)

    print("🤖 Roblox Studio AI Helper Plugin Loaded! Listening for commands...")
