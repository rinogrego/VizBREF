function generate_team_options(no_team){
    if (parseInt(no_team) == 1) {
        const player_1_team_select = document.querySelector('#player_1_team_select');
        // remove prior options
        player_1_team_select.innerHTML = '';

        // generate options
        const player_1_league = document.querySelector('#player_1_league_select');
        const league = player_1_league.options[player_1_league.selectedIndex].value;

        fetch('/data')
        .then(response => response.json())
        .then(data => Object.keys(data[`${league}`]).sort().forEach((tim) => {
            const team_option = document.createElement('option')
            team_option.value = `${tim}`;
            team_option.innerHTML = `${tim.replace('-', ' ')}`;
            player_1_team_select.appendChild(team_option)
        }))
    } else if (parseInt(no_team) == 2) {
        const player_2_team_select = document.querySelector('#player_2_team_select');
        // remove prior options
        player_2_team_select.innerHTML = '';

        // generate options
        const player_2_league = document.querySelector('#player_2_league_select');
        const league = player_2_league.options[player_2_league.selectedIndex].value;

        fetch('/data')
        .then(response => response.json())
        .then(data => Object.keys(data[`${league}`]).sort().forEach((tim) => {
            const team_option = document.createElement('option')
            team_option.value = `${tim}`;
            team_option.innerHTML = `${tim.replace('-', ' ')}`;
            player_2_team_select.appendChild(team_option)
        }))
    }

}

function generate_player_options(no_player){
    if (parseInt(no_player) == 1){
        const player_1_select = document.querySelector('#player_1_select');
        // remove prior options
        player_1_select.innerHTML = '';
        
        // get selected league
        const player_1_league = document.querySelector('#player_1_league_select');
        const league = player_1_league.options[player_1_league.selectedIndex].value;
        
        // generate options
        const player_1_team = document.querySelector('#player_1_team_select');
        const team = player_1_team.options[player_1_team.selectedIndex].value;

        // fetch(`/data/${team}`)
        fetch('/data')
        .then(response => response.json())
        .then(data => Object.values(data[`${league}`][`${team}`]).sort().forEach((pemain) => {
            const player_option = document.createElement('option')
            player_option.value = `${pemain}`;
            player_option.innerHTML = `${pemain.replace('-', ' ')}`;
            player_1_select.appendChild(player_option)
        }))
    } else if (parseInt(no_player) == 2) {
        const player_2_select = document.querySelector('#player_2_select');
        // remove prior options
        player_2_select.innerHTML = '';
        
        // get selected league
        const player_2_league = document.querySelector('#player_2_league_select');
        const league = player_2_league.options[player_2_league.selectedIndex].value;
        
        // generate options
        const player_2_team = document.querySelector('#player_2_team_select');
        const team = player_2_team.options[player_2_team.selectedIndex].value;

        // fetch(`/data/${team}`)
        fetch('/data')
        .then(response => response.json())
        .then(data => Object.values(data[`${league}`][`${team}`]).sort().forEach((pemain) => {
            const player_option = document.createElement('option')
            player_option.value = `${pemain}`;
            player_option.innerHTML = `${pemain.replace('-', ' ')}`;
            player_2_select.appendChild(player_option)
        }))
    }
}