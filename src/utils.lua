local Utils = {}
local Config = require("config")

-- Get the global IsaacAI object
local IsaacAI = _G.IsaacAI
if not IsaacAI then
    error("utils.lua: IsaacAI not found in _G – main.lua must set _G.IsaacAI")
end

function Utils.Log(msg)
    if not Config.DEBUG then return end
    -- Print to console
    print("[IsaacAI] " .. tostring(msg))

    -- Also write to file
    local success, result = pcall(function()
        local file = IsaacAI:OpenFile(Config.LOG_FILE, "a")
        if file then
            file:Write(os.date("%H:%M:%S") .. " " .. tostring(msg) .. "\n")
            file:Close()
            return true
        end
        return false
    end)
    
    if not success then
        print("[IsaacAI] ERROR: Failed to write to log file: " .. tostring(result))
    end
end

function Utils.EncodeJSON(obj, depth)
    depth = depth or 0
    if depth > 10 then
        return '"[max depth exceeded]"'
    end
    
    local t = type(obj)
    
    if t == "table" then
        local isArray = true
        local count = 0
        
        -- Check if it's an array
        for k, v in pairs(obj) do
            count = count + 1
            if type(k) ~= "number" or k ~= count then
                isArray = false
                break
            end
        end
        
        local parts = {}
        if isArray and count > 0 then
            -- Encode as array
            for i = 1, count do
                table.insert(parts, Utils.EncodeJSON(obj[i], depth + 1))
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            -- Encode as object
            for k, v in pairs(obj) do
                local key = tostring(k)
                -- Escape quotes in key
                key = key:gsub('"', '\\"')
                table.insert(parts, '"' .. key .. '":' .. Utils.EncodeJSON(v, depth + 1))
            end
            return "{" .. table.concat(parts, ",") .. "}"
        end
    elseif t == "string" then
        -- Escape special characters
        local escaped = obj:gsub('\\', '\\\\')
                          :gsub('"', '\\"')
                          :gsub('\n', '\\n')
                          :gsub('\r', '\\r')
                          :gsub('\t', '\\t')
        return '"' .. escaped .. '"'
    elseif t == "number" then
        -- Handle special numbers
        if obj ~= obj then return '"NaN"' end  -- NaN check
        if obj == math.huge then return '"Infinity"' end
        if obj == -math.huge then return '"-Infinity"' end
        -- Format with more precision
        return string.format("%.4f", obj)
    elseif t == "boolean" then
        return tostring(obj)
    else
        return "null"
    end
end

function Utils.Distance(x1, y1, x2, y2)
    local dx = x2 - x1
    local dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)
end

function Utils.NormalizeDirection(x, y)
    local len = math.sqrt(x * x + y * y)
    if len < 0.001 then return 0, 0 end
    return math.floor(x / len + 0.5), math.floor(y / len + 0.5)
end

function Utils.Clamp(value, min_val, max_val)
    if value < min_val then return min_val end
    if value > max_val then return max_val end
    return value
end

function Utils.ValidateAction(action)
    if not action then return false end
    if not Config.VALID_ACTIONS[action.move_x] then return false end
    if not Config.VALID_ACTIONS[action.move_y] then return false end
    if not Config.VALID_ACTIONS[action.shoot_x] then return false end
    if not Config.VALID_ACTIONS[action.shoot_y] then return false end
    return true
end

return Utils
