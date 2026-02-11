local ActionHandler = {}
local Config = require("config")
local Utils = require("src.utils")

local IsaacAI = _G.IsaacAI
if not IsaacAI then
    error("action_handler.lua: IsaacAI not found in _G")
end

local currentAction = { move_x = 0, move_y = 0, shoot_x = 0, shoot_y = 0 }
local actionTimestamp = 0
local framesSinceLastRead = 0

function ActionHandler.ReadAction()
    framesSinceLastRead = framesSinceLastRead + 1
    
    -- Only read every N frames to reduce file I/O
    if framesSinceLastRead < Config.ACTION_CHECK_INTERVAL then
        return currentAction
    end
    
    framesSinceLastRead = 0

    local success, result = pcall(function()
        local file = IsaacAI:OpenFile(Config.ACTION_FILE, "r")
        if not file then
            return nil, "Could not open action file"
        end

        local content = file:Read()
        file:Close()

        -- Early return if file is empty or just has empty JSON
        if not content or #content < 5 then
            return nil, "Empty content"
        end

        -- Parse the action
        local action = ActionHandler.ParseJSON(content)
        
        if not action then
            return nil, "Failed to parse JSON"
        end
        
        if not Utils.ValidateAction(action) then
            return nil, "Invalid action values"
        end
        
        return action, nil
    end)

    if success and result then
        currentAction = result
        actionTimestamp = Isaac.GetTime()
        if Config.DEBUG then
            Utils.Log(string.format("Action: M[%d,%d] S[%d,%d]", 
                currentAction.move_x, currentAction.move_y,
                currentAction.shoot_x, currentAction.shoot_y))
        end
    elseif not success then
        Utils.Log("Error reading action: " .. tostring(result))
    end

    return currentAction
end

function ActionHandler.ParseJSON(json)
    if not json or type(json) ~= "string" then
        return nil
    end
    
    -- Remove whitespace
    json = json:gsub("%s+", "")
    
    -- Extract values
    local move_x = tonumber(json:match('"move_x"%s*:%s*(-?%d+)'))
    local move_y = tonumber(json:match('"move_y"%s*:%s*(-?%d+)'))
    local shoot_x = tonumber(json:match('"shoot_x"%s*:%s*(-?%d+)'))
    local shoot_y = tonumber(json:match('"shoot_y"%s*:%s*(-?%d+)'))
    
    -- Check if we got all values
    if not move_x or not move_y or not shoot_x or not shoot_y then
        return nil
    end
    
    return {
        move_x = move_x,
        move_y = move_y,
        shoot_x = shoot_x,
        shoot_y = shoot_y
    }
end

-- Map our actions to Isaac's input actions
local function MapToInputAction(action_value, positive_button, negative_button)
    if action_value > 0 then
        return positive_button
    elseif action_value < 0 then
        return negative_button
    end
    return nil
end

function ActionHandler.HandleInput(entity, inputHook, buttonAction)
    if inputHook ~= InputHook.IS_ACTION_PRESSED then
        return nil  -- Let other input hooks work normally
    end
    
    local player = entity:ToPlayer()
    if not player or player:GetPlayerType() ~= 0 then
        return nil  -- Only control player 0
    end

    local action = currentAction
    if not action then return nil end
    
    -- Handle movement inputs
    if buttonAction == ButtonAction.ACTION_LEFT then
        return action.move_x == -1
    elseif buttonAction == ButtonAction.ACTION_RIGHT then
        return action.move_x == 1
    elseif buttonAction == ButtonAction.ACTION_UP then
        return action.move_y == -1
    elseif buttonAction == ButtonAction.ACTION_DOWN then
        return action.move_y == 1
    -- Handle shooting inputs
    elseif buttonAction == ButtonAction.ACTION_SHOOTLEFT then
        return action.shoot_x == -1
    elseif buttonAction == ButtonAction.ACTION_SHOOTRIGHT then
        return action.shoot_x == 1
    elseif buttonAction == ButtonAction.ACTION_SHOOTUP then
        return action.shoot_y == -1
    elseif buttonAction == ButtonAction.ACTION_SHOOTDOWN then
        return action.shoot_y == 1
    end
    
    -- Let other buttons work normally (bomb, item use, etc)
    return nil
end

function ActionHandler.GetCurrentAction()
    return currentAction
end

function ActionHandler.GetActionAge()
    return Isaac.GetTime() - actionTimestamp
end

return ActionHandler
