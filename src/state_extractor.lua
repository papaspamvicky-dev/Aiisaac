local StateExtractor = {}
local Config = require("config")
local Utils = require("src.utils")

function StateExtractor.GetPlayerData(player)
    if not player then return nil end
    local pos = player.Position
    local vel = player.Velocity
    return {
        x = pos.X,
        y = pos.Y,
        vx = vel.X,
        vy = vel.Y,
        hp = player:GetHearts() + player:GetSoulHearts(),
        max_hp = player:GetMaxHearts() + player:GetSoulHearts(),
        bombs = player:GetNumBombs(),
        keys = player:GetNumKeys(),
        coins = player:GetNumCoins(),
        charge = player:GetActiveCharge(),
        has_flight = player.CanFly
    }
end

function StateExtractor.GetEnemies()
    local enemies = {}
    local player = Isaac.GetPlayer(0)
    for _, entity in ipairs(Isaac.GetRoomEntities()) do
        if entity:IsActiveEnemy(false) and entity:IsVulnerableEnemy() then
            local pos = entity.Position
            local vel = entity.Velocity
            table.insert(enemies, {
                x = pos.X,
                y = pos.Y,
                vx = vel.X,
                vy = vel.Y,
                hp = entity.HitPoints,
                max_hp = entity.MaxHitPoints,
                type = entity.Type,
                variant = entity.Variant,
                subtype = entity.SubType,
                distance = Utils.Distance(player.Position.X, player.Position.Y, pos.X, pos.Y)
            })
            if #enemies >= Config.MAX_ENEMIES then break end
        end
    end
    return enemies
end

function StateExtractor.GetProjectiles()
    local projectiles = {}
    local player = Isaac.GetPlayer(0)
    for _, entity in ipairs(Isaac.GetRoomEntities()) do
        if entity.Type == EntityType.ENTITY_PROJECTILE then
            local pos = entity.Position
            local vel = entity.Velocity
            table.insert(projectiles, {
                x = pos.X,
                y = pos.Y,
                vx = vel.X,
                vy = vel.Y,
                distance = Utils.Distance(player.Position.X, player.Position.Y, pos.X, pos.Y),
                is_hostile = entity.SpawnerType ~= EntityType.ENTITY_PLAYER
            })
            if #projectiles >= Config.MAX_PROJECTILES then break end
        end
    end
    return projectiles
end

function StateExtractor.GetRoomInfo()
    local level = Game():GetLevel()
    local room = Game():GetRoom()
    return {
        type = room:GetType(),
        shape = room:GetRoomShape(),
        stage = level:GetStage(),
        stage_type = level:GetStageType(),
        is_clear = room:IsClear(),
        room_index = level:GetCurrentRoomIndex(),
        grid_size_x = room:GetGridSize(),
        grid_size_y = room:GetGridHeight()
    }
end

function StateExtractor.GetPickups()
    local pickups = {}
    local player = Isaac.GetPlayer(0)
    for _, entity in ipairs(Isaac.GetRoomEntities()) do
        if entity.Type == EntityType.ENTITY_PICKUP then
            local pos = entity.Position
            table.insert(pickups, {
                x = pos.X,
                y = pos.Y,
                variant = entity.Variant,
                subtype = entity.SubType,
                distance = Utils.Distance(player.Position.X, player.Position.Y, pos.X, pos.Y)
            })
            if #pickups >= Config.MAX_PICKUPS then break end
        end
    end
    return pickups
end

function StateExtractor.ExtractFullState(frame)
    local player = Isaac.GetPlayer(0)
    if not player then return nil end
    return {
        frame = frame,
        timestamp = Isaac.GetTime(),
        player = StateExtractor.GetPlayerData(player),
        enemies = StateExtractor.GetEnemies(),
        projectiles = StateExtractor.GetProjectiles(),
        pickups = StateExtractor.GetPickups(),
        room = StateExtractor.GetRoomInfo(),
        game = {
            seed = Game():GetSeeds():GetStartSeed(),
            -- Safe difficulty extraction
            difficulty = (Game().GetDifficultyLevel and Game():GetDifficultyLevel())
                         or (Game().GetDifficulty and Game():GetDifficulty())
                         or 0,
            challenge = Game():GetChallenge()
        }
    }
end

return StateExtractor