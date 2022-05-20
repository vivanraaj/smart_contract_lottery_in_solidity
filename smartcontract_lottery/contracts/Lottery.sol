// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

//inherit into our contract
contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players; //this make all the arrays payable
    address payable public recentWinner;
    uint256 public randomness; //keep track of the randomness
    uint256 public usdEntryFee;
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;

    //0
    //1
    //2

    uint256 public fee;
    bytes32 public keyhash;
    event RequestedRandomness(bytes32 requestId); // new line added. same principle as "enum" ?

    // below u put 2 diff constructors into one line?
    // take constructor of the left and pass to right?
    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED; // also means 1
        fee = _fee;
        keyhash = _keyhash;
    }

    function enter() public payable {
        //$50 min
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; //now its 18 decimals as price feed comes in 8 decimals
        // for %50, is $2000/ETH
        // solidity doesnt like decimals
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        //the ownable inherit from openzeppelin
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // below lines is not best way to get random numbers..... see notes
        // // below line is typecast to uint256.. we want pick random winner from random index..
        // // use keccak256 as hashing algo..
        // // take random number and mash them in hashing algo
        // // hashing algo is not random
        // // all the parameters inside is random
        // uint256(
        //     keccak256(
        //         abi.encodePacked(
        //             nonce, // nonce is predictavle (aka, transaction number)
        //             msg.sender, //msg.sender is predicatable
        //             block.difficulty, //can actually be manupilated by the miners
        //             block.timestamp // timestamp is predictable
        //         )
        //     )
        // ) % players.length;
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER; // so in this state, nothing else is going on
        bytes32 requestId = requestRandomness(keyhash, fee);
        // chainlink node call vrf coordinator and vrfcoordinator call fullfillrandomness
        // then chainlink will return the data to fullfillrandomness
        emit RequestedRandomness(requestId); //this event need to be emitted
    }

    //override keyword is to override original declaration of the fullfillrandomness function
    // as it was written in the vrfconsumerbase.sol file
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        //before process random number, check state
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You arent there yet!"
        );
        require(_randomness > 0, "random-not-found");
        //noew need pick random winners
        //players array are [1,2,3...]
        //use the modulus way to random the players
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];

        //now give the winner money?
        recentWinner.transfer(address(this).balance);
        // Reset lottery
        players = new address payable[](0); //new array of size zero
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
