-- IsaacAI Main Entry Point
local IsaacAI = RegisterMod("IsaacAI", 1)
_G.IsaacAI = IsaacAI   -- EXPORT to global

local Config = require("config")
local Utils = require("src.utils")
local StateExtractor = require("src.state_extractor")
local ActionHandler = require("src.action_handler")

local frameCount = 0
local lastStateWrite = 0
local initialized = false

function IsaacAI:Init()
    Utils.Log("=== IsaacAI Mod Initialized ===")
    initialized = true
    frameCount = 0
    lastStateWrite = 0
end

function IsaacAI:OnUpdate()
    if not initialized then return end
    
    frameCount = frameCount + 1
    
    -- Read actions from file
    local success, err = pcall(function()
        ActionHandler.ReadAction()
    end)
    
    if not success then
        Utils.Log("Error in action reading: " .. tostring(err))
    end
end

function IsaacAI:OnInputAction(entity, inputHook, buttonAction)
    if not initialized then return nil end
    
    local success, result = pcall(function()
        return ActionHandler.HandleInput(entity, inputHook, buttonAction)
    end)
    
    if not success then
        Utils.Log("Error in input handling: " .. tostring(result))
        return nil
    end
    
    return result
end

function IsaacAI:WriteState()
    local success, err = pcall(function()
        local state = StateExtractor.ExtractFullState(frameCount)
        if not state then 
            Utils.Log("Failed to extract state")
            return 
        end

        local json = Utils.EncodeJSON(state)
        if not json then
            Utils.Log("Failed to encode state to JSON")
            return
        end
        
        local file = IsaacAI:OpenFile(Config.STATE_FILE, "w")
        if file then
            file:Write(json)
            file:Close()
        else
            Utils.Log("Failed to open state file for writing")
        end
    end)
    
    if not success then
        Utils.Log("Error writing state: " .. tostring(err))
    end
end

function IsaacAI:OnRender()
    if not initialized then return end
    
    -- Write state at the configured interval
    if frameCount - lastStateWrite >= Config.FRAME_INTERVAL then
        self:WriteState()
        lastStateWrite = frameCount
    end

    if not Config.DEBUG then return end
    
    -- Debug visualization
    local success, err = pcall(function()
        local player = Isaac.GetPlayer(0)
        if not player then return end

        local action = ActionHandler.GetCurrentAction()
        local screenPos = Isaac.WorldToScreen(player.Position)
        
        -- Display current action
        Isaac.RenderText(
            string.format("AI: Move[%d,%d] Shoot[%d,%d] Frame:%d",
                action.move_x, action.move_y, 
                action.shoot_x, action.shoot_y,
                frameCount),
            screenPos.X - 60, screenPos.Y - 40, 
            1, 1, 1, 1
        )

        -- Visual indicators for movement
        local scale = 25
        if action.move_x ~= 0 or action.move_y ~= 0 then
            Isaac.RenderText("M", 
                screenPos.X + action.move_x * scale - 3,
                screenPos.Y + action.move_y * scale - 5, 
                0, 1, 0, 1)
        end
        
        -- Visual indicators for shooting
        if action.shoot_x ~= 0 or action.shoot_y ~= 0 then
            Isaac.RenderText("S", 
                screenPos.X + action.shoot_x * scale - 3,
                screenPos.Y + action.shoot_y * scale - 20, 
                1, 0, 0, 1)
        end

        -- Display enemy count
        local enemyCount = #StateExtractor.GetEnemies()
        local projCount = #StateExtractor.GetProjectiles()
        Isaac.RenderText(
            string.format("E:%d P:%d", enemyCount, projCount), 
            screenPos.X - 30, screenPos.Y - 55, 
            1, 1, 0, 1
        )
        
        -- Display action age (to detect stale actions)
        local actionAge = ActionHandler.GetActionAge()
        if actionAge > 1000 then  -- More than 1 second old
            Isaac.RenderText("STALE ACTION!", 
                screenPos.X - 40, screenPos.Y + 30, 
                1, 0, 0, 1)
        end
    end)
    
    if not success then
        Utils.Log("Error in render: " .. tostring(err))
    end
end

-- Register callbacks
IsaacAI:AddCallback(ModCallbacks.MC_POST_GAME_STARTED, IsaacAI.Init)
IsaacAI:AddCallback(ModCallbacks.MC_POST_UPDATE, IsaacAI.OnUpdate)
IsaacAI:AddCallback(ModCallbacks.MC_INPUT_ACTION, IsaacAI.OnInputAction)
IsaacAI:AddCallback(ModCallbacks.MC_POST_RENDER, IsaacAI.OnRender)

Utils.Log("IsaacAI main.lua loaded")
